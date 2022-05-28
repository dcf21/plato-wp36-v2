# -*- coding: utf-8 -*-
# tls.py

import logging
import multiprocessing
import numpy as np
from transitleastsquares import transitleastsquares

from plato_wp36.lightcurve import LightcurveArbitraryRaster

from typing import Optional


def process_lightcurve(lc: LightcurveArbitraryRaster, lc_duration: Optional[float], search_settings: dict,
                       thread_count: int = multiprocessing.cpu_count()):
    """
    Perform a transit search on a light curve, using the TLS code.

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
    :param thread_count:
        The number of parallel threads to use.
    :return:
        dict containing the results of the transit search.
    """

    # If requested, truncate the input lightcurve before we start processing it
    if lc_duration is not None:
        lc = lc.truncate_to_length(maximum_time=lc_duration)

    # Extract an array of times and fluxes from the lightcurve object
    time = lc.times
    flux = lc.fluxes

    # Fix normalisation
    flux_normalised = flux / np.mean(flux)
    logging.info("Lightcurve metadata: {}".format(lc.metadata))

    # Create a list of settings to pass to TLS
    tls_settings = {
        'use_threads': thread_count,
        'show_progress_bar': False
    }

    if 'period_min' in search_settings:
        tls_settings['period_min'] = float(search_settings['period_min'])  # Minimum trial period, days
    if 'period_max' in search_settings:
        tls_settings['period_max'] = float(search_settings['period_max'])  # Maximum trial period, days

    # Run this lightcurve through Transit Least Squares
    model = transitleastsquares(time, flux_normalised)
    results = model.power(**tls_settings)

    # Clean up results: Astropy Quantity objects are not serialisable
    # results = dict(results)
    #
    # for keyword in results:
    #     if isinstance(results[keyword], u.Quantity):
    #         value_quantity = results[keyword]
    #         value_numeric = value_quantity.value
    #         value_unit = str(value_quantity.unit)
    #
    #         if isinstance(value_numeric, np.ndarray):
    #             value_numeric = list(value_numeric)
    #
    #         results[keyword] = [value_numeric, value_unit]
    #
    #     elif isinstance(results[keyword], np.ndarray):
    #         value_numeric = list(results[keyword])
    #         results[keyword] = value_numeric

    # Work out how many transit we found
    transit_count = 0
    if isinstance(results.transit_times, list):
        transit_count = len(results.transit_times)

    # Return summary results
    results = {
        'period': results.period,
        'transit_count': transit_count,
        'depth': results.depth,
        'duration': results.duration,
        'sde': results.SDE
    }

    # Extended results to save to disk
    results_extended = results

    # Return results
    return results, results_extended
