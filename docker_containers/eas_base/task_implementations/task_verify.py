#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_verify.py

"""
Implementation of the EAS pipeline task <verify>.
"""

import argparse
import logging
import numpy as np

from typing import Dict

from plato_wp36 import lightcurve, logging_database, task_database, task_execution


def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    """
    Implementation of the EAS pipeline task <verify>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :param task_info:
        Object describing the task we are to execute.
    :param task_description:
        A dictionary of metadata containing all the configuration options supplied by the user for this task.
    :return:
        None
    """

    # Perform verification task

    # Open a connection to the task database
    task_db = task_database.TaskDatabaseConnection()

    # Read specification for the lightcurve we are to verify
    directory = task_info.working_directory
    filename = task_description['inputs']['lightcurve']

    logging.info("Running verification of <{}/{}>".format(directory, filename))

    # Read input lightcurve
    lc = lightcurve.LightcurveArbitraryRaster.from_file(directory=directory, filename=filename,
                                                        must_have_passed_qc=False)

    # Verify lightcurve
    output = {
        'verification_time_min': np.min(lc.times),
        'verification_time_max': np.max(lc.times),
        'verification_flux_min': np.min(lc.fluxes),
        'verification_flux_max': np.max(lc.fluxes)
    }

    logging.info("Lightcurve <{}/{}> time span {:.1f} to {:.1f}".format(directory, filename,
                                                                        output['verification_time_min'],
                                                                        output['verification_time_max']))

    logging.info("Lightcurve <{}/{}> flux range {:.6f} to {:.6f}".format(directory, filename,
                                                                         output['verification_flux_min'],
                                                                         output['verification_flux_max']))

    # Run first code for checking LCs
    error_count = lc.check_fixed_step(verbose=True, max_errors=4)

    if error_count == 0:
        logging.info("V1: Lightcurve <{}/{}> has fixed step".format(directory, filename))
        output['verification_v1'] = True
    else:
        logging.info("V1: Lightcurve <{}/{}> doesn't have fixed step ({:d} errors)".
                     format(directory, filename, error_count))
        output['verification_v1'] = False

    # Run second code for checking LCs
    error_count = lc.check_fixed_step_v2(verbose=True, max_errors=4)

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
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-id', required=True, type=int, dest='job_id',
                        help='The integer ID of the job in <eas_scheduling_attempt> table')
    args = parser.parse_args()

    # Set up logging, so that log messages are recorded in the EasControl database
    EasLoggingHandlerInstance = logging_database.EasLoggingHandler()

    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        handlers=[EasLoggingHandlerInstance, logging.StreamHandler()]
                        )

    # Start pipeline task
    task_execution.do_pipeline_task(job_id=args.job_id,
                                    eas_logger=EasLoggingHandlerInstance,
                                    task_handler=task_handler)
