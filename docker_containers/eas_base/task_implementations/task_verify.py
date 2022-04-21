#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_verify.py

"""
Implementation of the EAS pipeline task <verify>.
"""

import argparse
import logging
import numpy as np

from typing import Dict

from plato_wp36 import logging_database, task_database, task_execution


def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    # Perform verification task
    input_id = os.path.join(
        source.get('directory', 'test_lightcurves'),
        source.get('filename', 'lightcurve.dat')
    )

    logging.info("Verifying <{input_id}>.".format(input_id=input_id))

    # Read input lightcurve
    lc = self.read_lightcurve(source=source)

    # Verify lightcurve
    output = {
        'time_min': np.min(lc.times),
        'time_max': np.max(lc.times),
        'flux_min': np.min(lc.fluxes),
        'flux_max': np.max(lc.fluxes)
    }

    logging.info("Lightcurve <{}> time span {:.1f} to {:.1f}".format(input_id,
                                                                     output['time_min'],
                                                                     output['time_max']))

    logging.info("Lightcurve <{}> flux range {:.6f} to {:.6f}".format(input_id,
                                                                      output['flux_min'],
                                                                      output['flux_max']))

    # Run first code for checking LCs
    error_count = lc.check_fixed_step(verbose=True, max_errors=4)

    if error_count == 0:
        logging.info("V1: Lightcurve <{}> has fixed step".format(input_id))
        output['v1'] = True
    else:
        logging.info("V1: Lightcurve <{}> doesn't have fixed step ({:d} errors)".format(input_id, error_count))
        output['v1'] = False

    # Run second code for checking LCs
    error_count = lc.check_fixed_step_v2(verbose=True, max_errors=4)

    if error_count == 0:
        logging.info("V2: Lightcurve <{}> has fixed step".format(input_id))
        output['v2'] = True
    else:
        logging.info("V2: Lightcurve <{}> doesn't have fixed step ({:d} errors)".format(input_id, error_count))
        output['v2'] = False

    # Log output to results table
    result_log.record_result(job_name=job_name, target_name=input_id,
                             task_name='verify',
                             parameters=self.job_parameters, timestamp=start_time,
                             result=output)


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
