#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_binning.py

"""
Implementation of the EAS pipeline task <binning>.
"""

import logging
import numpy as np

from plato_wp36 import lightcurve, lightcurve_resample, task_database, task_execution


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <binning>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Perform rebinning task

    # Open a connection to the task database
    task_db = task_database.TaskDatabaseConnection()

    # Read specification for the lightcurve we are to verify
    directory = execution_attempt.task_object.working_directory
    filename_in = execution_attempt.task_object.task_description['inputs']['lightcurve']
    filename_out = execution_attempt.task_object.task_description['outputs']['lightcurve']
    cadence = float(execution_attempt.task_object.task_description['cadence'])

    logging.info("Running rebinning of <{}/{}> to <{}/{}>".format(directory, filename_in, directory, filename_out))

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
    # Run task
    task_handler()
