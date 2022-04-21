#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_binning.py

"""
Implementation of the EAS pipeline task <binning>.
"""

import argparse
import logging

from typing import Dict

from plato_wp36 import lightcurve_resample, logging_database, task_database, task_execution


def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    # Perform rebinning task
    input_id = os.path.join(
        source.get('directory', 'test_lightcurves'),
        source.get('filename', 'lightcurve.dat')
    )

    logging.info("Rebinning <{input_id}>.".format(input_id=input_id))

    # Read input lightcurve
    lc = self.read_lightcurve(source=source)

    # Re-bin lightcurve
    start_time = np.min(lc.times)
    end_time = np.max(lc.times)
    new_times = np.arange(start_time, end_time, cadence / 86400)  # Array of times (days)

    resampler = lightcurve_resample.LightcurveResampler(input_lc=lc)
    new_lc = resampler.onto_raster(output_raster=new_times)

    # Eliminate nasty edge effects
    new_lc.fluxes[0] = 1
    new_lc.fluxes[-1] = 1

    # Write output
    self.write_lightcurve(lightcurve=new_lc, target=target)


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
