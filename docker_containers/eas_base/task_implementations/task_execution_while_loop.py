#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_execution_while_loop.py

"""
Implementation of the EAS pipeline task <execution_while_loop>.
"""

import time

from plato_wp36 import task_database, task_execution


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <execution_while_loop>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Perform the null task
    time.sleep(10)


if __name__ == "__main__":
    # Run task
    task_handler()
