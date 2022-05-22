# -*- coding: utf-8 -*-
# exotrans.py

from plato_wp36.lightcurve import LightcurveArbitraryRaster

from typing import Optional


def process_lightcurve(lc: LightcurveArbitraryRaster, lc_duration: Optional[float], search_settings: dict):
    """
    Perform a transit search on a light curve, using the exotrans code.

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
    time = lc.times
    flux = lc.fluxes

    results = {}

    # Extended results to save to disk
    results_extended = results

    # Return results
    return results, results_extended
