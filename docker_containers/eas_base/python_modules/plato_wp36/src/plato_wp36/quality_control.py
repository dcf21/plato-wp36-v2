# -*- coding: utf-8 -*-
# quality_control.py

"""
Functions for computing quality control metrics. Many of these are rather arbitrarily defined currently.
"""

import numpy as np

from plato_wp36.lightcurve import LightcurveArbitraryRaster


def transit_detection_quality_control(lc: LightcurveArbitraryRaster, metadata: dict):
    """
    Determine whether the metadata returned by a transit-detection algorithm is a successful detection, or a failure.
    Currently the PLATO success criteria for transit detection are not tightly defined, so for the moment we use
    an arbitrary statistic - detecting the correct period to within 3%.

    :param lc:
        The lightcurve object containing the input lightcurve.
    :type lc:
        LightcurveArbitraryRaster
    :param metadata:
        The metadata dictionary returned by the transit-detection code.
    :type metadata:
        Dict
    :return:
        Updated metadata dictionary, with QC data added.
    """

    # Test success
    outcome = "UNDEFINED"
    target_period = np.nan
    if ('orbital_period' in lc.metadata) and ('period' in metadata):
        target_period = lc.metadata['orbital_period']
        observed_period = metadata['period']
        period_offset = target_period / observed_period

        # For now, pick an arbitrary target, of detection period to within 3%
        if 0.97 < period_offset < 1.03:
            outcome = "PASS"
        else:
            outcome = "FAIL"

    # Return summary results
    output_metadata = {
        'outcome': outcome,
        'target_period': target_period
    }

    return output_metadata
