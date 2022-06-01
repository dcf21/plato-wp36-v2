#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_execution_conditional.py

"""
Implementation of the EAS pipeline task <execution_conditional>.
"""

import json

from plato_wp36 import task_database, task_execution


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <execution_conditional>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Open a connection to the task database
    with task_database.TaskDatabaseConnection() as task_db:
        # Query value of conditional criterion
        criterion_true = bool(execution_attempt.task_object.task_description['criterion'])
        execution_path = 'task_list' if criterion_true else 'task_list_else'

        # Extract list of tasks in this execution chain
        if execution_path not in execution_attempt.task_object.task_description:
            return
        task_list = execution_attempt.task_object.task_description[execution_path]

        # Check that this execution chain is a list of task descriptors
        assert isinstance(task_list, list), "Execution chain has incorrect type of <{}>".format(type(task_list))

        # Schedule the selected execution path - create metadata for this task
        subtask_description = {
            'task_list': task_list
        }
        subtask_description_json = json.dumps(subtask_description)

        subtask_metadata = {
            **execution_attempt.task_object.metadata,
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
