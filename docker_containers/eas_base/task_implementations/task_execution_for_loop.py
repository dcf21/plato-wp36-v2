#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_execution_for_loop.py

"""
Implementation of the EAS pipeline task <execution_for_loop>, which runs an execution chain repeatedly in
a for loop.
"""

import json
from math import log10
import numpy as np

from plato_wp36 import task_database, task_execution


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <execution_for_loop>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Open a connection to the task database
    with task_database.TaskDatabaseConnection() as task_db:
        # Extract list of tasks in this execution chain
        if 'task_list' not in execution_attempt.task_object.task_description:
            return
        task_list = execution_attempt.task_object.task_description['task_list']

        # Check that this execution chain is a list of task descriptors
        assert isinstance(task_list, list), "Execution chain has incorrect type of <{}>".format(type(task_list))

        # Name of the metadata parameter we are to iterate over
        parameter_name = execution_attempt.task_object.task_description['name']

        # Work out all the parameter values we need to iterate over
        if 'values' in execution_attempt.task_object.task_description:
            parameter_values = execution_attempt.task_object.task_description['values']
        elif 'linear_range' in execution_attempt.task_object.task_description:
            parameter_values = np.linspace(execution_attempt.task_object.task_description['linear_range'][0],
                                           execution_attempt.task_object.task_description['linear_range'][1],
                                           execution_attempt.task_object.task_description['linear_range'][2]
                                           )
        elif 'log_range' in execution_attempt.task_object.task_description:
            parameter_values = np.logspace(log10(execution_attempt.task_object.task_description['log_range'][0]),
                                           log10(execution_attempt.task_object.task_description['log_range'][1]),
                                           execution_attempt.task_object.task_description['log_range'][2]
                                           )
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
                **execution_attempt.task_object.metadata,
                parameter_name: parameter_value,
                "{}_index".format(parameter_name): parameter_index,
                "task_description": subtask_description_json
            }

            # Create entry for this task
            task_db.task_register(parent_id=execution_attempt.task_object.task_id,
                                  job_name=execution_attempt.task_object.job_name,
                                  working_directory=execution_attempt.task_object.working_directory,
                                  task_type="execution_chain",
                                  metadata=subtask_metadata)


if __name__ == "__main__":
    # Run task
    task_handler()
