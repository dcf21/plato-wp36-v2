#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_synthesis_batman.py

"""
Implementation of the EAS pipeline task <synthesis_batman>.
"""

import logging

from typing import Dict

from plato_wp36 import task_database, task_execution
from eas_batman_wrapper.batman_wrapper import BatmanWrapper


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    """
    Implementation of the EAS pipeline task <synthesis_batman>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :param task_info:
        Object describing the task we are to execute.
    :param task_description:
        A dictionary of metadata containing all the configuration options supplied by the user for this task.
    :return:
        None
    """

    # Run synthesis task

    # Open a connection to the task database
    task_db = task_database.TaskDatabaseConnection()

    # Read specification for the lightcurve we are to synthesise
    specs = task_description.get('specs', {})
    directory = task_info.working_directory
    filename = task_description['outputs']['lightcurve']

    logging.info("Running batman synthesis of <{}/{}>".format(directory, filename))

    # Do synthesis
    synthesiser = BatmanWrapper()
    synthesiser.configure(**specs)
    lc_object = synthesiser.synthesise()
    synthesiser.close()

    # Write output
    lc_object.to_file(directory=directory, filename=filename, execution_id=execution_attempt.attempt_id)

    # Log lightcurve metadata to the database
    task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id, metadata=lc_object.metadata)

    # Close database
    task_db.commit()
    task_db.close_db()


if __name__ == "__main__":
    # Run task
    task_handler()
