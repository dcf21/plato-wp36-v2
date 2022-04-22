#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_multiply.py

"""
Implementation of the EAS pipeline task <multiply>.
"""

import argparse
import logging

from typing import Dict

from plato_wp36 import lightcurve, logging_database, task_database, task_execution


def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    """
    Implementation of the EAS pipeline task <multiply>.

    :param execution_attempt:
        Object describing this attempt by the job scheduler to run this task.
    :param task_info:
        Object describing the task we are to execute.
    :param task_description:
        A dictionary of metadata containing all the configuration options supplied by the user for this task.
    :return:
        None
    """

    # Perform multiplication task

    # Open a connection to the task database
    task_db = task_database.TaskDatabaseConnection()

    # Read specification for the lightcurve we are to verify
    directory = task_info.working_directory
    filename_1 = task_description['inputs']['lightcurve_1']
    filename_2 = task_description['inputs']['lightcurve_2']
    filename_out = task_description['outputs']['lightcurve']

    logging.info("Running multiplication of <{}/{}> and <{}/{}>".format(directory, filename_1, directory, filename_2))

    # Read input lightcurve
    lc_1 = lightcurve.LightcurveArbitraryRaster.from_file(directory=directory, filename=filename_1,
                                                          must_have_passed_qc=False)
    lc_2 = lightcurve.LightcurveArbitraryRaster.from_file(directory=directory, filename=filename_2,
                                                          must_have_passed_qc=False)

    # Multiply lightcurves together
    lc_result = lc_1 * lc_2

    # Write output
    lc_result.to_file(directory=directory, filename=filename_out, execution_id=execution_attempt.attempt_id)

    # Log lightcurve metadata to the database
    task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id, metadata=lc_result.metadata)

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
