#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_synthesise_platosim.py

"""
Quality control implementation of the EAS pipeline task <null>, which does nothing.

This is a useful template for the minimal code needed to create a new EAS module from scratch.
"""

import argparse
import logging

from typing import Dict

from plato_wp36 import logging_database, task_database, task_execution


def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    # Open a connection to the task database
    task_db = task_database.TaskDatabaseConnection()

    # Mark QC outcome
    for output_file in execution_attempt.output_files.values():
        task_db.file_version_update(product_version_id=output_file.product_version_id,
                                    passed_qc=True)

    task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id,
                                     all_products_passed_qc=True)

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
