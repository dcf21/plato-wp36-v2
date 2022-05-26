# -*- coding: utf-8 -*-
# qats.py

from math import floor, log
import logging
import numpy as np
import os
from subprocess import Popen, PIPE

from plato_wp36.lightcurve import LightcurveArbitraryRaster
from plato_wp36 import settings, task_execution, temporary_directory

from typing import Optional


def process_lightcurve(lc: LightcurveArbitraryRaster, lc_duration: Optional[float], search_settings: dict):
    """
    Perform a transit search on a light curve, using the QATS code.

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
    durations_days = np.linspace(0.05, 0.2, 5)  # days
    durations = durations_days / lc_time_step_days  # time steps

    # Minimum transit period, days
    minimum_period = 0.5  # days

    # Maximum transit period, days
    minimum_n_transits = 2
    maximum_period = lc_duration / minimum_n_transits  # days

    # Maximum TTV relative magnitude f
    f = 0.15
    sigma_spans = int(floor(log(maximum_period / minimum_period) / log(1 + f)))
    sigma_base = minimum_period / lc_time_step_days  # time steps

    # Logging
    logging.info("QATS testing {:d} transit lengths".format(len(durations)))
    logging.info("QATS testing {} sigma spans".format(sigma_spans))

    # Keep track of the S and M values returned each time we run QATS
    qats_output = []
    s_maximum = 0
    s_maximum_index = None

    # Store lightcurve to a text file in a temporary directory
    with temporary_directory.TemporaryDirectory() as tmp_dir:
        lc_file = os.path.join(tmp_dir.tmp_dir, "lc.dat")

        # Store lightcurve to text file
        np.savetxt(lc_file, lc_fixed_step.fluxes)

        # Loop over all values of q
        for transit_length in durations:
            for sigma_index in range(0, sigma_spans):
                # Equation 15
                sigma_min = int(sigma_base * pow(1 + f / 2, sigma_index))

                # Equation 16
                sigma_max = int(sigma_base * pow(1 + f / 2, sigma_index + 1))

                # Run QATS
                qats_path = os.path.join(eas_settings.settings['pythonPath'],
                                         "../../data/datadir_local/qats/qats/call_qats")

                # logging.info("{} {} {} {} {}".format(qats_path, lc_file, sigma_min, sigma_max, transit_length))

                qats_ok, qats_stdout = task_execution.call_subprocess_and_catch_stdout(
                    arguments=(qats_path, lc_file, sigma_min, sigma_max, transit_length)
                )

                if qats_ok:
                    # QATS returned no error; loop over lines of output and read S_best and M_best
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

                                qats_output.append({
                                    's_best': s_best,
                                    'm_best': m_best,
                                    'sigma_min': sigma_min,
                                    'sigma_max': sigma_max,
                                    'transit_length': transit_length
                                })

                                if s_best > s_maximum:
                                    s_maximum = s_best
                                    s_maximum_index = len(qats_output) - 1
                            except ValueError:
                                logging.warning("Could not parse QATS output")

        # Now fetch the best-fit sequence of transits
        transit_list = []
        if s_maximum_index is not None:
            x = qats_output[s_maximum_index]

            # Run QATS
            qats_path = os.path.join(eas_settings.settings['pythonPath'],
                                     "../../data/datadir_local/qats/qats/call_qats_indices")

            qats_ok, qats_stdout = task_execution.call_subprocess_and_catch_stdout(
                arguments=(qats_path, lc_file, x['m_best'], x['sigma_min'], x['sigma_max'], x['transit_length'])
            )

            if qats_ok:
                # QATS returned no error; loop over lines of output and read S_best and M_best
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

    # Deduce mean period from list of transit times
    best_period = np.nan
    if len(transit_list) > 1:
        first_transit = transit_list[0]['time']
        last_transit = transit_list[-1]['time']
        period_span = len(transit_list) - 1
        best_period = (last_transit - first_transit) / period_span

    # Find best period
    results = {
        'period': best_period
    }

    # Extended results to save to disk
    results_extended = results

    # Return results
    return results, results_extended
