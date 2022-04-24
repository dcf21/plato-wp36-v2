#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_execution_for_loop.py

"""
Quality control implementation of the EAS pipeline task <execution_for_loop>.
"""

from typing import Dict

from plato_wp36 import task_database, task_execution


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    """
    Implementation of the QC validation process which happens after the EAS pipeline task <execution_for_loop>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :param task_info:
        Object describing the task we are to execute.
    :param task_description:
        A dictionary of metadata containing all the configuration options supplied by the user for this task.
    :return:
        None
    """

    # Open a connection to the task database
    task_db = task_database.TaskDatabaseConnection()

    # Mark QC outcome
    for output_file in execution_attempt.output_files.values():
        task_db.file_version_update(product_version_id=output_file.product_version_id,
                                    passed_qc=True)

    task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id,
                                     all_products_passed_qc=True)

    # Close database
    task_db.commit()
    task_db.close_db()


if __name__ == "__main__":
    # Run task
    task_handler()
