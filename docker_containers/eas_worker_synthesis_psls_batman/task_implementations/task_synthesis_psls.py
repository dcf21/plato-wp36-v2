#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_synthesis_psls.py

"""
Implementation of the EAS pipeline task <synthesis_psls>.
"""

import logging
import os

from plato_wp36 import task_database, task_execution, temporary_directory
from eas_psls_wrapper.psls_wrapper import PslsWrapper


@task_execution.eas_pipeline_task
def task_handler(execution_attempt: task_database.TaskExecutionAttempt):
    """
    Implementation of the EAS pipeline task <synthesis_psls>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :return:
        None
    """

    # Open a connection to the task database
    with task_database.TaskDatabaseConnection() as task_db:
        # Read specification for the lightcurve we are to synthesise
        lc_specs = execution_attempt.task_info.task_description.get('specs', {})
        filename = execution_attempt.task_info.task_description['outputs']['lightcurve']

        logging.info("Running PSLS synthesis of <{}>".format(filename))

        # Do synthesis
        synthesiser = PslsWrapper()
        synthesiser.configure(**lc_specs)
        lc_object = synthesiser.synthesise()
        synthesiser.close()

        # Create a temporary directory to store the LC in, until it is imported into the file repository
        with temporary_directory.TemporaryDirectory as tmp_dir:
            tmp_path = os.path.join(tmp_dir, filename)
            file_metadata = lc_object.to_file(target_path=tmp_path)

            # Import lightcurve into the task database
            task_db.execution_attempt_register_output(
                execution_attempt=execution_attempt,
                output_name="lightcurve",
                file_path=tmp_path,
                preserve=False,
                metadata={**lc_object.metadata, **file_metadata}
            )

        # Associate lightcurve metadata to the synthesis task in the task database
        task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id,
                                         metadata=lc_object.metadata)


if __name__ == "__main__":
    # Run task
    task_handler()
