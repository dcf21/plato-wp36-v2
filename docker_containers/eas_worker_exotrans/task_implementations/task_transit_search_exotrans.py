#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_transit_search_exotrans.py

"""
Implementation of the EAS pipeline task <transit_search_exotrans>.
"""

import logging

from typing import Dict

from plato_wp36 import quality_control, lightcurve, task_database, task_execution
from eas_exotrans_wrapper import exotrans


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    """
    Implementation of the EAS pipeline task <transit_search_exotrans>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :param task_info:
        Object describing the task we are to execute.
    :param task_description:
        A dictionary of metadata containing all the configuration options supplied by the user for this task.
    :return:
        None
    """

    # Perform the transit detection task

    # Read specification for the lightcurve we are to verify
    directory = task_info.working_directory
    filename_in = task_description['inputs']['lightcurve']
    lc_duration = float(task_description['lc_duration'])

    logging.info("Running <{directory}/{filename}> through Exotrans with duration {lc_days:.1f}.".format(
        directory=directory, filename=filename_in, lc_days=lc_duration)
    )

    # Read input lightcurve
    lc_in = lightcurve.LightcurveArbitraryRaster.from_file(directory=directory, filename=filename_in,
                                                           must_have_passed_qc=True)

    # Process lightcurve
    search_settings = task_description.get('search_settings', {})
    x = exotrans.process_lightcurve(lc=lc_in, lc_duration=lc_duration, search_settings=search_settings)

    # Extract output
    output, output_extended = x

    # Test whether transit-detection was successful
    quality_control.transit_detection_quality_control(lc=lc_in, metadata=output)

    # Add additional metadata to results
    for item in ['integrated_transit_power', 'pixels_in_transit', 'pixels_in_transit', 'mes']:
        output[item] = lc_in.metadata.get(item, None)

    # Open a connection to the task database
    task_db = task_database.TaskDatabaseConnection()

    # Log outcome metadata to the database
    task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id, metadata=lc_result.metadata)

    # Close database
    task_db.commit()
    task_db.close_db()


if __name__ == "__main__":
    # Run task
    task_handler()
