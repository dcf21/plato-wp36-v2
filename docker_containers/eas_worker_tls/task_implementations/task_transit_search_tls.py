#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# task_transit_search_tls.py

"""
Implementation of the EAS pipeline task <transit_search_tls>.
"""

import argparse
import logging
import time

from typing import Dict

from plato_wp36 import logging_database, task_database, task_execution


def task_handler(execution_attempt: task_database.TaskExecutionAttempt,
                 task_info: task_database.Task,
                 task_description: Dict):
    # Perform the transit detection task
    input_id = os.path.join(
        source.get('directory', 'test_lightcurves'),
        source.get('filename', 'lightcurve.dat')
    )

    logging.info("Running <{input_id}> through <{tda_name}> with duration {lc_days:.1f}.".format(
        input_id=input_id,
        tda_name=tda_name,
        lc_days=lc_duration)
    )

    # Record start time
    start_time = time.time()

    # Read input lightcurve
    lc = self.read_lightcurve(source=source)

    # Process lightcurve
    if tda_name == 'bls_reference':
        x = bls_reference.process_lightcurve(lc=lc, lc_duration=lc_duration, search_settings=search_settings)
    elif tda_name == 'bls_kovacs':
        x = bls_kovacs.process_lightcurve(lc=lc, lc_duration=lc_duration, search_settings=search_settings)
    elif tda_name == 'dst_v26':
        x = dst_v26.process_lightcurve(lc=lc, lc_duration=lc_duration, search_settings=search_settings)
    elif tda_name == 'dst_v29':
        x = dst_v29.process_lightcurve(lc=lc, lc_duration=lc_duration, search_settings=search_settings)
    elif tda_name == 'exotrans':
        x = exotrans.process_lightcurve(lc=lc, lc_duration=lc_duration, search_settings=search_settings)
    elif tda_name == 'qats':
        x = qats.process_lightcurve(lc=lc, lc_duration=lc_duration, search_settings=search_settings)
    elif tda_name == 'tls':
        x = tls.process_lightcurve(lc=lc, lc_duration=lc_duration, search_settings=search_settings)
    else:
        assert False, "Unknown transit-detection code <{}>".format(tda_name)

        # Extract output
        output, output_extended = x

    # Test whether transit-detection was successful
    quality_control(lc=lc, metadata=output)

    # Add additional metadata to results
    for item in ['integrated_transit_power', 'pixels_in_transit', 'pixels_in_transit', 'mes']:
        output[item] = lc.metadata.get(item, None)

    # Send result to message queue
    result_log.record_result(job_name=job_name, tda_code=tda_name, target_name=input_id,
                             task_name='transit_detection',
                             parameters=self.job_parameters, timestamp=start_time,
                             result=output, result_extended=output_extended)


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
