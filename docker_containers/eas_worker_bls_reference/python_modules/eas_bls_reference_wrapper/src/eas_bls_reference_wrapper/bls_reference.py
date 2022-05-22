# -*- coding: utf-8 -*-
# bls_reference.py

import numpy as np
from astropy import units as u
from astropy.timeseries import BoxLeastSquares

from plato_wp36.lightcurve import LightcurveArbitraryRaster

from typing import Optional


def process_lightcurve(lc: LightcurveArbitraryRaster, lc_duration: Optional[float], search_settings: dict):
    """
    Perform a transit search on a light curve, using the bls_reference code.

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

    # Extract an array of times and fluxes from the lightcurve object
    t = lc.times * u.day
    y_filt = lc.fluxes

    # Work out what period range we are scanning
    minimum_period = float(search_settings.get('period_min', 0.5)) * u.day
    maximum_period = float(search_settings.get('period_max', lc.duration() / 2)) * u.day

    # Run this lightcurve through the astropy implementation of BLS
    durations = np.linspace(0.05, 0.2, 10) * u.day
    model = BoxLeastSquares(t, y_filt)
    results = model.autopower(durations,
                              minimum_period=minimum_period,
                              maximum_period=maximum_period,
                              minimum_n_transit=2,
                              frequency_factor=2.0)

    # Find best period
    best_period = results.period[np.argmax(results.power)]
    results = {
        'period': float(best_period / u.day),
        'power': np.max(results.power)
    }

    # Extended results to save to disk
    results_extended = results

    # Return results
    return results, results_extended
