#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_synthesis_psls.py

"""
Implementation of the EAS pipeline task <synthesis_psls>.
"""

import logging
import os

from typing import Dict

from plato_wp36 import task_database, task_execution, temporary_directory
from eas_psls_wrapper.psls_wrapper import PslsWrapper


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    """
    Implementation of the EAS pipeline task <synthesis_psls>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :param task_info:
        Object describing the task we are to execute.
    :param task_description:
        A dictionary of metadata containing all the configuration options supplied by the user for this task.
    :return:
        None
    """

    # Run synthesis task

    # Open a connection to the task database
    with task_database.TaskDatabaseConnection() as task_db:
        # Read specification for the lightcurve we are to synthesise
        specs = task_description.get('specs', {})
        directory = task_info.working_directory
        filename = task_description['outputs']['lightcurve']

        logging.info("Running PSLS synthesis of <{}/{}>".format(directory, filename))

        # Do synthesis
        synthesiser = PslsWrapper()
        synthesiser.configure(**specs)
        lc_object = synthesiser.synthesise()
        synthesiser.close()

        # Write output
        with temporary_directory.TemporaryDirectory as tmp_dir:
            tmp_path = os.path.join(tmp_dir, filename)
            file_metadata = lc_object.to_file(target_path=tmp_path)

            # Find out what file product this lightcurve corresponds to
            product_ids = task_db.file_product_by_filename(directory=directory, filename=filename)
            assert len(product_ids) > 0, \
                ("This lightcurve <{}/{}> does not correspond to any file product in the database".
                 format(directory, filename))
            product_id = product_ids[0]

            # Import lightcurve into the task database
            task_db.file_version_register(product_id=product_id,
                                          generated_by_task_execution=execution_attempt.attempt_id,
                                          file_path_input=tmp_path,
                                          preserve=False,
                                          metadata={**lc_object.metadata, **file_metadata}
                                          )

        # Associate lightcurve metadata to the synthesis task in the task database
        task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id,
                                         metadata=lc_object.metadata)



if __name__ == "__main__":
    # Run task
    task_handler()
