# -*- coding: utf-8 -*-
# task_execution.py

"""
Wrapper for the functions that perform EAS pipeline tasks.

This is performs housekeeping tasks that are common to all tasks, such as recording log messages in the EasControl
task database, recording the execution times of tasks, and sending heartbeat messages to indicate that a task is still
running.
"""

import argparse
import json
import logging
import os
import sys
import subprocess
import traceback

from typing import Callable, Iterable

from plato_wp36 import logging_database, task_database, task_expression_evaluation
from plato_wp36 import task_heartbeat, task_objects, task_timer


def call_subprocess_and_log_output(arguments: Iterable):
    """
    Execute a shell command, and capture any error messages sent to stderr, storing them in the logging database.
    
    :param arguments:
        A list of the command-line arguments to run in the shell.
    :return:
        Boolean indicating whether the process exited with no error reported
    """

    # Run subprocess
    return call_subprocess_and_catch_stdout(arguments=arguments)[0]


def call_subprocess_and_catch_stdout(arguments: Iterable):
    """
    Execute a shell command, and capture any error messages sent to stderr, storing them in the logging database.

    :param arguments:
        A list of the command-line arguments to run in the shell.
    :return:
        Boolean indicating whether the process exited with no error reported
    """

    # Run subprocess
    string_arguments = [str(item) for item in arguments]
    process_output = subprocess.run(string_arguments, capture_output=True)

    # Check if subprocess exited with non-zero status, and log it
    if process_output.returncode != 0:
        logging.error("Executed subprocess returned error code {:d}".format(process_output.returncode))

    # Check if subprocess produced any output on stderr
    stderr_string = process_output.stderr.decode('utf-8').strip()
    if len(stderr_string) > 0:
        logging.warning("Executed subprocess produced stderr output:\n{:s}".format(stderr_string))

    # Return True is no error
    return process_output.returncode == 0, process_output.stdout


def eas_pipeline_task(
        task_handler: Callable[[task_database.TaskExecutionAttempt], None],

):
    """
    Perform an EAS pipeline task, reading the task configuration from the process's getargs.

    :param task_handler:
        The function we should call to perform the pipeline task. It is passed three arguments:
        task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                     task_info: task_database.Task,
                     task_description: Dict)
    :return:
        Callable[None, None]
    """

    def wrapped_pipeline_task():
        # Read command-line arguments
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('--job-id', required=True, type=int, dest='job_id',
                            help='The integer ID of the job in <eas_scheduling_attempt> table')
        args = parser.parse_args()

        # Set up logging, so that log messages are recorded in the EasControl database
        EasLoggingHandlerInstance = logging_database.EasLoggingHandler()

        # Output all logging messages - even errors - to stdout, not stderr
        # If we output them to stderr, then the end up in the logging database twice, as the calling process will
        # pick them up.
        logging.basicConfig(level=logging.INFO,
                            format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                            datefmt='%d/%m/%Y %H:%M:%S',
                            handlers=[EasLoggingHandlerInstance, logging.StreamHandler(stream=sys.stdout)]
                            )

        # Is this a QC task?
        is_qc_task = "task_qc_implementations" in os.path.abspath(sys.argv[0])

        # Start pipeline task
        do_pipeline_task(job_id=args.job_id,
                         is_qc_task=is_qc_task,
                         eas_logger=EasLoggingHandlerInstance,
                         task_handler=task_handler)

    return wrapped_pipeline_task


def do_pipeline_task(job_id: int,
                     is_qc_task: bool,
                     task_handler: Callable[[task_database.TaskExecutionAttempt], None],
                     eas_logger: logging_database.EasLoggingHandler):
    """
    Perform the EAS pipeline task.

    :param job_id:
        The integer ID of the job in <eas_scheduling_attempt> table. This allows us to fetch all the
        metadata associated with the job we are to perform.
    :param is_qc_task:
        Boolean flag indicating whether this is a QC task.
    :param task_handler:
        The function we should call to perform the pipeline task. It is passed three arguments:
        task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                     task_info: task_database.Task,
                     task_description: Dict)
    :param eas_logger:
        The <EasLoggingHandler> which is connected to this task's logging stream, which will direct log messages
        to the EasControl database.
    :return:
        None
    """

    # Make sure all the logging messages we send to the log database, reference the job we are working on
    eas_logger.set_task_attempt_id(attempt_id=job_id)

    # Task type string which we show in log messages
    task_type = "QC" if is_qc_task else "task execution"

    # Catch all exceptions, and record them in the logging database
    try:
        # Start task timer. Do not remove this, as otherwise the start and end times for the job are not recorded.
        with task_timer.TaskTimer(task_attempt_id=job_id):
            # Announce that we're running a task
            logging.info("Starting {} attempt <{}> in child process".format(task_type, job_id))

            # Launch a child process to send heartbeat updates to show this job is still running. Do not remove this,
            # as otherwise the task scheduler will believe that this task has crashed.
            with task_heartbeat.TaskHeartbeat(task_attempt_id=job_id):
                # Open a connection to the EasControl task database
                with task_database.TaskDatabaseConnection() as task_db:
                    # Fetch the task description for the job we are to work on
                    attempt_info = task_db.execution_attempt_lookup(attempt_id=job_id, embed_task_object=True)

                    if attempt_info is None:
                        logging.warning("Scheduling attempt <{}> has disappeared from the database!".format(job_id))
                        return

                    # Extract the JSON code describing the task to execute
                    task_description_json = attempt_info.task_object.metadata.get('task_description', None)

                    # Check we have a task description specified
                    if type(task_description_json) != task_objects.MetadataItem:
                        raise ValueError("Task does not have a task description supplied in its metadata.")

                    # Extract task description from JSON
                    task_description_raw = json.loads(task_description_json.value)

                    # Evaluate any metadata expressions within our task description
                    expression_evaluator = task_expression_evaluation.TaskExpressionEvaluation(
                        metadata=attempt_info.task_object.metadata
                    )
                    task_description = expression_evaluator.evaluate_in_structure(structure=task_description_raw)

                    # Set task description within Task object
                    attempt_info.task_object.task_description = task_description

                    # If an explicit job name is specified in the task description, update the job name of this task
                    if 'job_name' in task_description:
                        attempt_info.task_object.job_name = task_description['job_name']

                    # If an explicit working directory is specified in the task description, update the task descriptor
                    if 'working_directory' in task_description:
                        attempt_info.task_object.working_directory = task_description['working_directory']

                # Launch task handler
                task_handler(attempt_info)

    except Exception:
        error_message = traceback.format_exc()
        logging.error(error_message)

        # Open a connection to the EasControl task database
        with task_database.TaskDatabaseConnection() as task_db:
            # Record the failure of this task
            task_db.execution_attempt_update(attempt_id=job_id, error_fail=True, error_text=error_message)

    # Announce that we've finished running a task
    logging.info("Finished {} attempt <{}> in child process".format(task_type, job_id))
