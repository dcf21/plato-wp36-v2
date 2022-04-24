#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_multiply.py

"""
Implementation of the EAS pipeline task <multiply>.
"""

import logging

from typing import Dict

from plato_wp36 import lightcurve, task_database, task_execution


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    """
    Implementation of the EAS pipeline task <multiply>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :param task_info:
        Object describing the task we are to execute.
    :param task_description:
        A dictionary of metadata containing all the configuration options supplied by the user for this task.
    :return:
        None
    """

    # Perform multiplication task

    # Open a connection to the task database
    task_db = task_database.TaskDatabaseConnection()

    # Read specification for the lightcurve we are to verify
    directory = task_info.working_directory
    filename_1 = task_description['inputs']['lightcurve_1']
    filename_2 = task_description['inputs']['lightcurve_2']
    filename_out = task_description['outputs']['lightcurve']

    logging.info("Running multiplication of <{}/{}> and <{}/{}>".format(directory, filename_1, directory, filename_2))

    # Read input lightcurve
    lc_1 = lightcurve.LightcurveArbitraryRaster.from_file(directory=directory, filename=filename_1,
                                                          must_have_passed_qc=False)
    lc_2 = lightcurve.LightcurveArbitraryRaster.from_file(directory=directory, filename=filename_2,
                                                          must_have_passed_qc=False)

    # Multiply lightcurves together
    lc_result = lc_1 * lc_2

    # Write output
    lc_result.to_file(directory=directory, filename=filename_out, execution_id=execution_attempt.attempt_id)

    # Log lightcurve metadata to the database
    task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id, metadata=lc_result.metadata)

    # Close database
    task_db.commit()
    task_db.close_db()


if __name__ == "__main__":
    # Run task
    task_handler()
