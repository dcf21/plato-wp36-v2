#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_multiply.py

"""
Implementation of the EAS pipeline task <multiply>.
"""

import logging

from plato_wp36 import lightcurve, task_database, task_execution, temporary_directory


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <multiply>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Perform multiplication task

    # Read specification for the lightcurve we are to verify
    directory = execution_attempt.task_object.working_directory
    filename_1 = execution_attempt.task_object.task_description['inputs']['lightcurve_1']
    filename_2 = execution_attempt.task_object.task_description['inputs']['lightcurve_2']
    filename_out = execution_attempt.task_object.task_description['outputs']['lightcurve']

    logging.info("Running multiplication of <{}/{}> and <{}/{}>".format(directory, filename_1, directory, filename_2))

    # Read input lightcurve
    with temporary_directory.TemporaryDirectory() as tmp_dir:
        with task_database.TaskDatabaseConnection() as task_db:
            lc_in_filename, lc_in_metadata = task_db.task_open_file_input(
                task=execution_attempt.task_object,
                tmp_dir=tmp_dir,
                input_name="lightcurve_1"
            )
        lc_in_1 = lightcurve.LightcurveArbitraryRaster.from_file(
            file_path=lc_in_filename,
            file_metadata=lc_in_metadata
        )

        with task_database.TaskDatabaseConnection() as task_db:
            lc_in_filename, lc_in_metadata = task_db.task_open_file_input(
                task=execution_attempt.task_object,
                tmp_dir=tmp_dir,
                input_name="lightcurve_2"
            )
        lc_in_2 = lightcurve.LightcurveArbitraryRaster.from_file(
            file_path=lc_in_filename,
            file_metadata=lc_in_metadata
        )

    # Multiply lightcurves together
    lc_result = lc_in_1 * lc_in_2

    # Write output
    lc_result.to_file(directory=directory, filename=filename_out, execution_id=execution_attempt.attempt_id)

    # Log lightcurve metadata to the database
    with task_database.TaskDatabaseConnection() as task_db:
        task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id, metadata=lc_result.metadata)


if __name__ == "__main__":
    # Run task
    task_handler()
