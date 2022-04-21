#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_multiply.py

"""
Implementation of the EAS pipeline task <multiply>.
"""

import argparse
import logging
import time

from typing import Dict

from plato_wp36 import logging_database, task_database, task_execution


def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    # Perform multiplication task
    out_id = os.path.join(
        output.get('directory', 'test_lightcurves'),
        output.get('filename', 'lightcurve.dat')
    )

    logging.info("Multiplying lightcurves")

    # Load lightcurve 1
    lc_1 = self.read_lightcurve(source=input_1)

    # Load lightcurve 2
    lc_2 = self.read_lightcurve(source=input_2)

    # Multiply lightcurves together
    result = lc_1 * lc_2

    # Store result
    self.write_lightcurve(lightcurve=result, target=output)


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
