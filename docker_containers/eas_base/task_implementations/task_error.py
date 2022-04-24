#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_error.py

"""
Implementation of the EAS pipeline task <error>, which simply produces an error message.
This is only really useful for testing that the error logging procedures work properly.
"""

from typing import Dict

from plato_wp36 import task_database, task_execution


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    """
    Implementation of the EAS pipeline task <error>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :param task_info:
        Object describing the task we are to execute.
    :param task_description:
        A dictionary of metadata containing all the configuration options supplied by the user for this task.
    :return:
        None
    """

    # Perform the error task
    assert False


if __name__ == "__main__":
    # Run task
    task_handler()
