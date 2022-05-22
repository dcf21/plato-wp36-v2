#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_verify.py

"""
Implementation of the EAS pipeline task <verify>.
"""

import logging
import numpy as np

from plato_wp36 import lightcurve, task_database, task_execution, temporary_directory


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <verify>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Perform verification task

    # Read specification for the lightcurve we are to verify
    directory = execution_attempt.task_object.working_directory
    filename = execution_attempt.task_object.task_description['inputs']['lightcurve']

    logging.info("Running verification of <{}/{}>".format(directory, filename))

    # Read input lightcurve
    with temporary_directory.TemporaryDirectory() as tmp_dir:
        with task_database.TaskDatabaseConnection() as task_db:
            lc_in_filename, lc_in_metadata = task_db.task_open_file_input(
                task=execution_attempt.task_object,
                tmp_dir=tmp_dir,
                input_name="lightcurve"
            )
        lc_in = lightcurve.LightcurveArbitraryRaster.from_file(
            file_path=lc_in_filename,
            file_metadata=lc_in_metadata
        )

    # Verify lightcurve
    output = {
        'verification_time_min': np.min(lc_in.times),
        'verification_time_max': np.max(lc_in.times),
        'verification_flux_min': np.min(lc_in.fluxes),
        'verification_flux_max': np.max(lc_in.fluxes)
    }

    logging.info("Lightcurve <{}/{}> time span {:.1f} to {:.1f}".format(directory, filename,
                                                                        output['verification_time_min'],
                                                                        output['verification_time_max']))

    logging.info("Lightcurve <{}/{}> flux range {:.6f} to {:.6f}".format(directory, filename,
                                                                         output['verification_flux_min'],
                                                                         output['verification_flux_max']))

    # Run code for checking LCs have a fixed step
    error_count = lc_in.check_fixed_step(verbose=True, max_errors=4)

    if error_count == 0:
        logging.info("Lightcurve <{}/{}> has fixed step".format(directory, filename))
        output['verification'] = True
    else:
        logging.info("Lightcurve <{}/{}> doesn't have fixed step ({:d} errors)".
                     format(directory, filename, error_count))
        output['verification'] = False

    # Log lightcurve metadata to the database
    with task_database.TaskDatabaseConnection() as task_db:
        task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id, metadata=output)


if __name__ == "__main__":
    # Run task
    task_handler()
