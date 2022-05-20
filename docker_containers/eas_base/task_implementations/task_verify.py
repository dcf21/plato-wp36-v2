#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_verify.py

"""
Implementation of the EAS pipeline task <verify>.
"""

import logging
import numpy as np

from typing import Dict

from plato_wp36 import lightcurve, task_database, task_execution


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
    with task_database.TaskDatabaseConnection() as task_db:
        lc_in_file_handle, lc_in_metadata = task_db.task_open_file_input(
            task=execution_attempt.task_object,
            input_name="lightcurve"
        )
    lc_in = lightcurve.LightcurveArbitraryRaster.from_file(
        file_handle=lc_in_file_handle,
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

    # Run first code for checking LCs
    error_count = lc_in.check_fixed_step(verbose=True, max_errors=4)

    if error_count == 0:
        logging.info("V1: Lightcurve <{}/{}> has fixed step".format(directory, filename))
        output['verification_v1'] = True
    else:
        logging.info("V1: Lightcurve <{}/{}> doesn't have fixed step ({:d} errors)".
                     format(directory, filename, error_count))
        output['verification_v1'] = False

    # Run second code for checking LCs
    error_count = lc_in.check_fixed_step_v2(verbose=True, max_errors=4)

    if error_count == 0:
        logging.info("V2: Lightcurve <{}/{}> has fixed step".format(directory, filename))
        output['verification_v2'] = True
    else:
        logging.info("V2: Lightcurve <{}/{}> doesn't have fixed step ({:d} errors)".
                     format(directory, filename, error_count))
        output['verification_v2'] = False

    # Log lightcurve metadata to the database
    task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id, metadata=output)

    # Close database
    task_db.commit()
    task_db.close_db()


if __name__ == "__main__":
    # Run task
    task_handler()
