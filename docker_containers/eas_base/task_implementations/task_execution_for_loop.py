#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_execution_for_loop.py

"""
Implementation of the EAS pipeline task <execution_for_loop>, which runs an execution chain repeatedly in
a for loop.
"""

import argparse
import json
import logging
from math import log10
import numpy as np
# noinspection PyUnresolvedReferences
import random

from typing import Dict

import plato_wp36.constants
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

    # Name of the metadata parameter we are to iterate over
    parameter_name = task_description['name']

    # These constants may be used in evaluating the for loop parameter range
    # noinspection PyUnusedLocal
    constants = plato_wp36.constants.EASConstants()

    # Work out all the parameter values we need to iterate over
    if 'values' in task_description:
        parameter_values = [eval(str(val)) for val in task_description['values']]
    elif 'linear_range' in task_description:
        parameter_values = np.linspace(eval(str(task_description['linear_range'][0])),
                                       eval(str(task_description['linear_range'][1])),
                                       eval(str(task_description['linear_range'][2])))
    elif 'log_range' in task_description:
        parameter_values = np.logspace(log10(eval(str(task_description['log_range'][0]))),
                                       log10(eval(str(task_description['log_range'][1]))),
                                       eval(str(task_description['log_range'][2])))
    else:
        raise ValueError(
            "Iteration values should be specified as either <values>, <linear_range> or <log_range"
        )

    # Schedule each iteration in turn
    for parameter_index, parameter_value in enumerate(parameter_values):
        # Create metadata for this task
        subtask_description = {
            'task_list': task_list
        }
        subtask_description_json = json.dumps(subtask_description)

        subtask_metadata = {
            **task_info.metadata,
            parameter_name: parameter_value,
            "{}_index".format(parameter_name): parameter_index,
            "task_description": subtask_description_json
        }

        # Create entry for this task
        task_db.task_register(parent_id=task_info.task_id,
                              job_name=task_info.job_name,
                              working_directory=task_info.working_directory,
                              task_type="execution_chain",
                              metadata=subtask_metadata)

    # Close database
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
