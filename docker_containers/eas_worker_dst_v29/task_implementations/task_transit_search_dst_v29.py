#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_transit_search_dst_v29.py

"""
Implementation of the EAS pipeline task <transit_search_dst_v29>.
"""

import logging

from plato_wp36 import quality_control, lightcurve, task_database, task_execution
from eas_dst_v29_wrapper import dst_v26


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <transit_search_dst_v29>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Perform the transit detection task

    # Read specification for the lightcurve we are to verify
    directory = execution_attempt.task_object.working_directory
    filename_in = execution_attempt.task_object.task_description['inputs']['lightcurve']
    lc_duration = float(execution_attempt.task_object.task_description['lc_duration'])

    logging.info("Running <{directory}/{filename}> through DST v29 with duration {lc_days:.1f}.".format(
        directory=directory, filename=filename_in, lc_days=lc_duration)
    )

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

    # Process lightcurve
    search_settings = execution_attempt.task_object.task_description.get('search_settings', {})
    x = dst_v29.process_lightcurve(lc=lc_in, lc_duration=lc_duration, search_settings=search_settings)

    # Extract output
    dst_output, output_extended = x

    # Test whether transit-detection was successful
    qc_metadata = quality_control.transit_detection_quality_control(lc=lc_in, metadata=dst_output)

    # Propagate some metadata from input lightcurve to transit-detection results
    for item in ['integrated_transit_power', 'pixels_in_transit', 'pixels_in_transit', 'mes']:
        dst_output[item] = lc_in.metadata.get(item, None)

    # Open a connection to the task database
    with task_database.TaskDatabaseConnection() as task_db:
        # Log outcome metadata to the database
        task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id,
                                         metadata={**dst_output, **qc_metadata})


if __name__ == "__main__":
    # Run task
    task_handler()
