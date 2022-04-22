#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_binning.py

"""
Implementation of the EAS pipeline task <binning>.
"""

import argparse
import logging
import numpy as np

from typing import Dict

from plato_wp36 import lightcurve, lightcurve_resample, logging_database, task_database, task_execution


def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    """
    Implementation of the EAS pipeline task <binning>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :param task_info:
        Object describing the task we are to execute.
    :param task_description:
        A dictionary of metadata containing all the configuration options supplied by the user for this task.
    :return:
        None
    """

    # Perform rebinning task

    # Open a connection to the task database
    task_db = task_database.TaskDatabaseConnection()

    # Read specification for the lightcurve we are to verify
    directory = task_info.working_directory
    filename_in = task_description['inputs']['lightcurve']
    filename_out = task_description['outputs']['lightcurve']
    cadence = float(task_description['cadence'])

    logging.info("Running rebinning of <{}/{}> to <{}/{}>".format(directory, filename_in, directory, filename_out))

    # Read input lightcurve
    lc_in = lightcurve.LightcurveArbitraryRaster.from_file(directory=directory, filename=filename_in,
                                                           must_have_passed_qc=True)

    # Re-bin lightcurve
    start_time = np.min(lc_in.times)
    end_time = np.max(lc_in.times)
    new_times = np.arange(start_time, end_time, cadence / 86400)  # Array of times (days)

    resampler = lightcurve_resample.LightcurveResampler(input_lc=lc_in)
    lc_output = resampler.onto_raster(output_raster=new_times)

    # Eliminate nasty edge effects
    lc_output.fluxes[0] = 1
    lc_output.fluxes[-1] = 1

    # Write output
    lc_output.to_file(directory=directory, filename=filename_out, execution_id=execution_attempt.attempt_id)

    # Log lightcurve metadata to the database
    task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id, metadata=lc_output.metadata)

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
