#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_execution_do_while_loop.py

"""
Implementation of the EAS pipeline task <execution_do_while_loop>.
"""

import json
import logging

from plato_wp36 import task_database, task_execution, task_expression_evaluation
from plato_wp36.task_objects import MetadataItem


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <execution_do_while_loop>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Open a connection to the task database
    with task_database.TaskDatabaseConnection() as task_db:
        # Fetch task description
        td = execution_attempt.task_object.task_description

        # Extract list of tasks in this execution chain
        if 'task_list' not in td:
            return
        task_list = td['task_list']

        # Check that this execution chain is a list of task descriptors
        assert isinstance(task_list, list), "Execution chain has incorrect type of <{}>".format(type(task_list))

        # Fetch iteration counter
        iteration_name = td['iteration_name']
        iteration_counter_name = "{}_index".format(iteration_name)
        iteration_counter = execution_attempt.task_object.metadata.get(iteration_counter_name, 0)
        if isinstance(iteration_counter, MetadataItem):
            iteration_counter = iteration_counter.value

        # Test whether we iterate again
        already_iterating = iteration_counter > 0
        if already_iterating:
            logging.info("Considering whether to repeat do loop")
            expression_evaluator = task_expression_evaluation.TaskExpressionEvaluation(
                metadata=execution_attempt.task_object.metadata,
                requested_metadata=execution_attempt.task_object.input_metadata
            )
            repeat_criterion = expression_evaluator.evaluate_expression(expression=td['repeat_criterion'])

            if not repeat_criterion:
                logging.info("Do loop completed after iteration {:d}".format(int(iteration_counter)))
                return
            else:
                logging.info("Do loop continuing for another cycle after iteration {:d}".format(int(iteration_counter)))
        else:
            logging.info("Entering do loop for the first time")

        # *** Run another iteration ***

        # Append task to the end of the loop which decides whether to do another iteration
        task_list.append({
            "task": "execution_do_while_loop",
            "iteration_name": td['iteration_name'],
            "requires_metadata_from": td['requires_metadata_from_child'],
            "requires_metadata_from_child": td['requires_metadata_from_child'],
            "repeat_criterion": td['repeat_criterion'],
            "task_list": task_list[:]
        })

        # Create metadata for execution chain to run another iteration
        subtask_description = {
            'task_list': task_list
        }
        subtask_description_json = json.dumps(subtask_description)

        subtask_metadata = {
            **execution_attempt.task_object.metadata,
            iteration_counter_name: iteration_counter + 1,
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
