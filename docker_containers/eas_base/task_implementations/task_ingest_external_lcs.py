#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_ingest_external_lcs.py

"""
Implementation of the EAS pipeline task <ingest_external_lcs>, which imports lightcurves from external data sets.
"""

import glob
import logging
import os
import time

from typing import Optional

from plato_wp36 import lc_reader_lcsg, task_database, task_execution, temporary_directory, settings
from plato_wp36.lightcurve import Lightcurve


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <ingest_external_lcs>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Perform the ingest_external_lcs task

    # Fetch EAS pipeline settings
    s = settings.Settings()

    # Read the format type of the lightcurves we are to import
    default_in_type = "lcsg"
    lc_in_type = execution_attempt.task_object.task_description.get('lc_type', default_in_type)

    # Make sure we recognise the specified input lightcurve format
    # Allowed formats are:
    # 'lcsg' - Lightcurves produced for the lightcurve stitching group by Oscar Barragan
    assert lc_in_type in ['lcsg']

    # Read path within <datadir_input> to the LCs we are to import
    default_in_path = "lightcurves_v2/csvs/bright/plato_bright*"
    lc_in_path = execution_attempt.task_object.task_description.get('input_path', default_in_path)

    # Logging update
    logging.info("Importing LCs in format <{}> from <{}>".format(lc_in_type, lc_in_path))

    # Create list of all input lightcurves
    lightcurve_list = sorted(glob.glob(os.path.join(s.settings['lcPath'], lc_in_path)))

    # Report number of lightcurves
    logging.info("Importing a total of {:d} lightcurves".format(len(lightcurve_list)))

    # Import each lightcurve in turn
    for lc_counter, lc_filename in enumerate(lightcurve_list):
        lc_name = os.path.split(lc_filename)[1]
        logging.info("Importing LC <{}>".format(lc_name))

        # Import lightcurve
        lc_object: Optional[Lightcurve] = None

        if lc_in_type == "lcsg":
            lc_object = lc_reader_lcsg.read_lcsg_lightcurve(file_path=lc_filename)

        # Check that we imported lightcurve
        assert lc_object is not None

        # Check whether this lightcurve already exists in the database
        with task_database.TaskDatabaseConnection() as task_db:
            # Look for matching file product
            item_directory = execution_attempt.task_object.working_directory
            matching_file_products = task_db.file_product_by_filename(
                directory=item_directory, filename=lc_name
            )

            # Check that output file product does not already exist in the database
            if len(matching_file_products) != 0:
                logging.info("Skipping lightcurve as it is already in the database.")

            # Create file product entry for this lightcurve
            semantic_type = "lightcurve_{:5d}".format(lc_counter)
            task_db.file_product_register(generator_task=execution_attempt.task_object.task_id,
                                          directory=item_directory,
                                          filename=lc_name,
                                          semantic_type=semantic_type,
                                          planned_time=time.time(),
                                          mime_type="null")

            # Create a temporary directory to store the LC in, until it is imported into the file repository
            with temporary_directory.TemporaryDirectory() as tmp_dir:
                tmp_path = os.path.join(tmp_dir.tmp_dir, lc_name)
                file_metadata = lc_object.to_file(target_path=tmp_path)

                # Create entry in the task's description for this output file product
                execution_attempt.task_object.task_description['outputs'] = {}
                execution_attempt.task_object.task_description['outputs'][semantic_type] = lc_name

                # Create file product version entry for this lightcurve
                task_db.execution_attempt_register_output(
                    execution_attempt=execution_attempt,
                    output_name=semantic_type,
                    file_path=tmp_path,
                    preserve=False,
                    file_metadata={**lc_object.metadata, **file_metadata}
                )


if __name__ == "__main__":
    # Run task
    task_handler()
