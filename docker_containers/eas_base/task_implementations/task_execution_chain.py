#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_execution_chain.py

"""
Implementation of the EAS pipeline task <execution_chain>, which simply executes a series of sub-tasks in order.
"""

import argparse
import json
import logging
import time

from typing import Dict

from plato_wp36 import logging_database, task_database, task_execution, task_objects


def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    # Open a connection to the task database
    task_db = task_database.TaskDatabaseConnection()

    # Extract list of tasks in this execution chain
    if 'task_list' not in task_description:
        return
    task_list = task_description['task_list']

    # Check that this execution chain is a list of task descriptors
    assert isinstance(task_list, list), "Execution chain has incorrect type of <{}>".format(type(task_list))

    # Schedule each task in turn
    for sub_task in task_list:
        # Check that this task descriptor is a dictionary, and specifies a task type
        assert isinstance(sub_task, dict), "Task description has incorrect type of <{}>".format(type(sub_task))
        assert 'task' in sub_task, "Task description has missing field 'task'."
        subtask_type = sub_task['task']

        # Identify all the file products that this task depends on
        subtask_file_inputs = []
        if 'inputs' in sub_task:
            assert isinstance(sub_task['inputs'], dict)
            for semantic_type, filename in sub_task['inputs'].items():
                matching_file_products = task_db.file_product_by_filename(directory=task_info.working_directory,
                                                                          filename=filename)

                # Check that input file product exists in the database
                if len(matching_file_products) != 1:
                    raise ValueError("Task <{}> could not find input <{}/{}>".
                                     format(subtask_type, task_info.working_directory, filename))

                # Add this required file input to the list of dependencies
                subtask_file_inputs.append([semantic_type, matching_file_products[0]])

        # Identify all the file products that this task will create, and make sure they don't already exist
        subtask_file_outputs = []
        if 'outputs' in sub_task:
            assert isinstance(sub_task['outputs'], dict)
            for semantic_type, filename in sub_task['outputs'].items():
                matching_file_products = task_db.file_product_by_filename(directory=task_info.working_directory,
                                                                          filename=filename)

                # Check that output file product does not already exist in the database
                if len(matching_file_products) != 0:
                    raise ValueError("Task <{}> creates pre-existing file <{}/{}>".
                                     format(subtask_type, task_info.working_directory, filename))

                # Add this required file input to the list of dependencies
                subtask_file_outputs.append([semantic_type, task_info.working_directory, filename])

        # Create JSON description for this task
        subtask_json_description = json.dumps(sub_task)

        # Create metadata for this task
        subtask_metadata = {
            **task_info.metadata,
            "task_description": subtask_json_description
        }

        # Create entry for this task
        subtask_id = task_db.task_register(parent_id=task_info.task_id,
                                           job_name=task_info.job_name,
                                           working_directory=task_info.working_directory,
                                           task_type=subtask_type,
                                           metadata=subtask_metadata)

        # Create entries declaring all the required file inputs
        for subtask_file_input in subtask_file_inputs:
            semantic_type_id = task_db.semantic_type_get_id(name=subtask_file_input[0])
            required_product_id = subtask_file_input[1]

            task_db.conn.execute("""
INSERT INTO eas_task_input (taskId, inputId, semanticType) VALUES (%s, %s, %s);
""", (subtask_id, required_product_id, semantic_type_id))

        # Create entries for all the file products this task will create
        for subtask_file_output in subtask_file_outputs:
            task_db.file_product_register(generator_task=subtask_id,
                                          directory=subtask_file_output[1],
                                          filename=subtask_file_output[2],
                                          semantic_type=subtask_file_output[0],
                                          planned_time=time.time(),
                                          mime_type="null")

    # Close database connection
    task_db.commit()
    task_db.close_db()


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-id', required=True, type=int, dest='job_id',
                        help='The integer ID of the job in <eas_scheduling_attempt> table')
    args = parser.parse_args()

    # Set up logging, so that log messages are recorded in the EasControl database
    EasLoggingHandlerInstance = logging_database.EasLoggingHandler()

    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        handlers=[EasLoggingHandlerInstance, logging.StreamHandler()]
                        )

    # Start pipeline task
    task_execution.do_pipeline_task(job_id=args.job_id,
                                    eas_logger=EasLoggingHandlerInstance,
                                    task_handler=task_handler)
