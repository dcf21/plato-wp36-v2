# -*- coding: utf-8 -*-
# qats.py

import glob
import logging
import numpy as np
import os
import dask

from math import floor, log, sqrt
from multiprocessing.pool import ThreadPool
from typing import Dict, Optional

from plato_wp36.lightcurve import LightcurveArbitraryRaster
from plato_wp36 import settings, task_database, task_execution, temporary_directory

# Keep track of the S and M values returned each time we run QATS
# Storing these as global variables is not thread-safe, but unfortunately is the only way to make them
# accessible to many dask threads working on the same call to <process_lightcurve>. This is fine so
# long as the calling process doesn't make multiple parallel calls to <process_lightcurve>.
qats_output: Dict[str, Dict[str, float]] = {}
s_maximum: float = 0.
s_maximum_index: Optional[str] = None


@dask.delayed
def dask_thread(qats_path, lc_file, delta_min, delta_max, transit_length):
    global qats_output, s_maximum, s_maximum_index

    run_key = "{}_{}_{}".format(delta_min, delta_max, transit_length)

    # logging.info("{} {} {} {} {}".format(qats_path, lc_file, delta_min, delta_max, transit_length))

    qats_ok, qats_stdout = task_execution.call_subprocess_and_catch_stdout(
        arguments=(qats_path, lc_file, delta_min, delta_max, transit_length)
    )

    if qats_ok:
        # QATS returned no error
        # Loop over lines of output and read S_best and M_best
        for line in qats_stdout.decode('utf-8').split('\n'):
            line = line.strip()
            # Ignore comment lines
            if (len(line) < 1) or (line[0] == '#'):
                continue

            # Split line into words
            words = line.split()
            if len(words) == 2:
                try:
                    s_best = float(words[0])  # Signal strength of best-fit transit sequence
                    m_best = int(words[1])  # Number of transits in best-fit sequence

                    # The QATS paper is ambiguous whether this is required, but it gives better results
                    s_best /= sqrt(m_best * transit_length)

                    qats_output[run_key] = {
                        's_best': s_best,
                        'm_best': m_best,
                        'delta_min': delta_min,
                        'delta_max': delta_max,
                        'transit_length': transit_length
                    }

                    if s_best > s_maximum:
                        s_maximum = s_best
                        s_maximum_index = run_key
                except ValueError:
                    logging.warning("Could not parse QATS output")


def process_lightcurve(lc: LightcurveArbitraryRaster, lc_duration: Optional[float], search_settings: dict):
    """
    Perform a transit search on a light curve, using the QATS code.

    This wrapper is quite inefficient, since it spends a lot of time forking child processes.

    :param lc:
        The lightcurve object containing the input lightcurve.
    :type lc:
        LightcurveArbitraryRaster
    :param lc_duration:
        If set, then the input lightcurve is truncated to a certain number of days before being processed.
    :type lc_duration:
        float
    :param search_settings:
        Dictionary of settings which control how we search for transits.
    :type search_settings:
        dict
    :return:
        dict containing the results of the transit search.
    """

    # Reset global variables
    global qats_output, s_maximum, s_maximum_index
    qats_output = {}
    s_maximum = 0.
    s_maximum_index = None

    # Fetch EAS pipeline settings to find out how many threads are allocated to each TLS worker
    with task_database.TaskDatabaseConnection() as task_db:
        qats_thread_assigned = task_db.container_get_resource_assignment(container_name='eas_worker_qats')['cpu']
        qats_thread_count = max(1, int(qats_thread_assigned))
    logging.info("QATS using {:d} threads".format(qats_thread_count))

    # If requested, truncate the input lightcurve before we start processing it
    if lc_duration is not None:
        lc = lc.truncate_to_length(maximum_time=lc_duration)

    # Look up EAS pipeline settings
    eas_settings = settings.Settings()

    # Convert input lightcurve to a fixed time step, and fill in gaps
    lc_fixed_step = lc.to_fixed_step()

    # Median subtract lightcurve
    median = np.median(lc_fixed_step.fluxes)
    lc_fixed_step.fluxes -= median

    # Normalise lightcurve
    std_dev = np.std(lc_fixed_step.fluxes)
    lc_fixed_step.fluxes /= std_dev

    # List of transit durations to consider
    lc_time_step_days = lc_fixed_step.time_step  # days
    duration_min = float(search_settings.get('duration_min', 0.05))  # days
    duration_max = float(search_settings.get('duration_max', 0.2))  # days
    duration_count = int(search_settings.get('duration_count', 16))
    durations_days = np.linspace(duration_min, duration_max, duration_count)  # days
    durations = durations_days / lc_time_step_days  # time steps

    # Minimum transit period, days
    period_min = search_settings.get('period_min', 4)  # days

    # Maximum transit period, days
    minimum_n_transits = int(search_settings.get('min_transit_count', 2))
    maximum_period = lc_duration / minimum_n_transits  # days

    # Maximum TTV relative magnitude f
    max_ttv_mag = float(search_settings.get('max_ttv_mag', 0.0005))
    delta_spans = int(floor(log(maximum_period / period_min) / log(1 + max_ttv_mag / 2)))
    delta_base = period_min / lc_time_step_days  # time steps

    # Logging
    logging.info("QATS testing {:d} transit lengths".format(len(durations)))
    logging.info("QATS testing {} delta spans".format(delta_spans))

    # Path to the QATS binary
    qats_path = os.path.join(eas_settings.settings['pythonPath'],
                             "../../data/datadir_local/qats/qats/call_qats")

    # Store lightcurve to a text file in a temporary directory
    with temporary_directory.TemporaryDirectory() as tmp_dir:
        lc_file = os.path.join(tmp_dir.tmp_dir, "lc.dat")

        # Store lightcurve to single-column text file without scientific notation
        np.savetxt(lc_file, lc_fixed_step.fluxes, fmt='%f')

        # Loop over all values of q
        delayed_processes = []
        for transit_length in durations:
            for delta_index in range(0, delta_spans):
                # Equation 15
                delta_min = int(delta_base * pow(1 + max_ttv_mag / 2, delta_index))

                # Equation 16
                delta_max = int(delta_base * pow(1 + max_ttv_mag / 2, delta_index + 1))

                # Ignore grid points with zero span in period
                if delta_min == delta_max:
                    continue

                # Run QATS
                delayed_processes.append(dask_thread(qats_path, lc_file, delta_min, delta_max, transit_length))

        # Run delayed processes
        dask.config.set(pool=ThreadPool(qats_thread_count))
        dask.compute(delayed_processes)

        # Produce output file with all the results
        with open(os.path.join(tmp_dir.tmp_dir, "grid.qats"), "wt") as f:
            ordered_rows = sorted(qats_output.values(), key=lambda x: x['s_best'], reverse=True)
            for row in ordered_rows:
                f.write("{s_best:15.5f} {m_best:5d} {delta_min:15.5f} {delta_max:15.5f} {transit_length:15.5f}\n".
                        format(**row))

        # Now fetch the best-fit sequence of transits
        transit_list = []
        if s_maximum_index is not None:
            x = qats_output[s_maximum_index]

            # Report results
            logging.info("Best fit: S={:.1f} ; M={:.0f}; transit length={:.2f} days".
                         format(s_maximum, x['m_best'], x['transit_length'] * lc_time_step_days))

            # Run QATS
            qats_path = os.path.join(eas_settings.settings['pythonPath'],
                                     "../../data/datadir_local/qats/qats/call_qats_indices")

            qats_ok, qats_stdout = task_execution.call_subprocess_and_catch_stdout(
                arguments=(qats_path, lc_file, x['m_best'], x['delta_min'], x['delta_max'], x['transit_length'])
            )

            if qats_ok:
                # QATS returned no error

                # Save output
                with open(os.path.join(tmp_dir.tmp_dir, "final.qats"), "wb") as f:
                    f.write(qats_stdout)

                # Loop over lines of output and read S_best and M_best
                for line in qats_stdout.decode('utf-8').split('\n'):
                    line = line.strip()
                    # Ignore comment lines
                    if (len(line) < 1) or (line[0] == '#'):
                        continue

                    # Split line into words
                    words = line.split()
                    if len(words) == 2:
                        try:
                            counter = int(words[0])  # Transit number
                            position = int(words[1])  # Position within time sequence

                            transit_list.append({
                                'counter': counter,
                                'position': position,
                                'time': lc_fixed_step.get_time_of_point(index=position)
                            })
                        except ValueError:
                            logging.warning("Could not parse QATS indices output")

        # Store tarball of debugging files
        cwd = os.getcwd()
        os.chdir(tmp_dir.tmp_dir)
        # logging.info(task_execution.call_subprocess_and_catch_stdout("ls".split())[1])
        task_execution.call_subprocess_and_catch_stdout(
            ["tar", "cvfz", "/tmp/qats_debugging.tar.gz"] + glob.glob("*.qats")
        )
        os.chdir(cwd)

    # Start building output data structure
    results = {
        'period': 0,
        'transit_count': len(transit_list),
        'period_span': len(transit_list) - 1
    }

    # Deduce mean period from list of transit times
    if len(transit_list) > 1:
        results['first_transit'] = transit_list[0]['time']
        results['last_transit'] = transit_list[-1]['time']
        results['period'] = (results['last_transit'] - results['first_transit']) / results['period_span']

    # Extended results
    results_extended = results

    # Return results
    return results, results_extended
