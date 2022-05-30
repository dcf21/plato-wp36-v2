#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_transit_search_tls.py

"""
Implementation of the EAS pipeline task <transit_search_tls>.
"""

import logging

from plato_wp36 import quality_control, lightcurve, settings, task_database, task_execution, temporary_directory
from eas_tls_wrapper import tls


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <transit_search_tls>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Perform the transit detection task

    # Fetch EAS pipeline settings to find out how many threads are allocated to each TLS worker
    with task_database.TaskDatabaseConnection() as task_db:
        task_type_list = task_db.task_type_list_from_db()
        tls_thread_count = max(1, int(task_type_list.worker_containers['eas_worker_tls']['cpu']))
    logging.info("TLS using {:d} threads".format(tls_thread_count))

    # Read specification for the lightcurve we are to verify
    filename_in = execution_attempt.task_object.task_description['inputs']['lightcurve']
    lc_duration = float(execution_attempt.task_object.task_description['lc_duration'])

    logging.info("Running <{filename}> through TLS with duration {lc_days:.1f}.".format(
        filename=filename_in, lc_days=lc_duration)
    )

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

    # Search for transits in this lightcurve
    transit_search_settings = execution_attempt.task_object.task_description.get('search_settings', {})
    x = tls.process_lightcurve(lc=lc_in,
                               lc_duration=lc_duration,
                               search_settings=transit_search_settings,
                               thread_count=tls_thread_count
                               )

    # Extract output returned by TLS
    tls_output, output_extended = x

    # Test whether transit-detection was successful
    qc_metadata = quality_control.transit_detection_quality_control(lc=lc_in, metadata=tls_output)

    # Propagate some metadata from input lightcurve to transit-detection results
    for item in ['integrated_transit_power', 'pixels_in_transit', 'pixels_in_transit', 'mes']:
        tls_output[item] = lc_in.metadata.get(item, None)

    # Open a connection to the task database
    with task_database.TaskDatabaseConnection() as task_db:
        # Log outcome metadata to the database
        task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id,
                                         metadata={**tls_output, **qc_metadata})


if __name__ == "__main__":
    # Run task
    task_handler()
