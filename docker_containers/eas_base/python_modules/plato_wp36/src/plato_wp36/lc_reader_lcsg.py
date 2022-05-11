# -*- coding: utf-8 -*-
# lc_reader_lcsg.py

"""
Read the ASCII lightcurves generated by the lightcurve stitching group, and turn them into Lightcurve objects.
"""

import numpy as np
import os
import re
import gzip

from typing import Optional

from .lightcurve import LightcurveArbitraryRaster
from .settings import Settings


def read_lcsg_lightcurve(filename: str, gzipped: bool = True, cut_off_time: Optional[float] = None,
                         directory: str = "lightcurves_v2"):
    """
    Read a lightcurve from an ASCII data file.

    ASCII file should have three columns:
    time [days] ; flux ; flag

    :param filename:
        The filename of the input data file.
    :type filename:
        str
    :param gzipped:
        Boolean flag indicating whether the input datafiles have been gzipped
    :type gzipped:
        bool
    :param cut_off_time:
        Only read lightcurve up to some cut off time
    :type cut_off_time:
        float
    :param directory:
        The directory in which the LCSG lightcurves are stored.
    :type directory:
        str
    :return:
        A <LightcurveArbitraryRaster> object.
    """

    times = []  # days
    fluxes = []
    uncertainties = []
    flags = []
    metadata = {
        'directory': directory,
        'filename': filename
    }

    # Fetch EAS settings
    settings = Settings().settings

    # Full path for this lightcurve
    file_path = os.path.join(settings['lcPath'], directory, filename)

    # Look up file open function
    file_opener = gzip.open if gzipped else open

    # Loop over lines of input file
    with file_opener(file_path, "rt") as file:
        for line in file:
            # Ignore blank lines and comment lines
            if len(line) == 0 or line[0] == '#':
                # Check for metadata item
                test = re.match(r"# #(.*)=(.*)", line)
                if test is not None:
                    metadata_key = test.group(1).strip()
                    metadata_value = test.group(2).strip()

                    # If metadata value is a float, convert it to a float. Otherwise keep it as string.
                    try:
                        metadata_value = float(metadata_value)
                    except ValueError:
                        pass

                    metadata[metadata_key] = metadata_value

                # ... otherwise ignore this line
                continue

            # Unpack data
            words = line.split(',')
            time = float(words[0])  # days
            flux = float(words[1])
            flag = float(words[2])
            uncertainty = 0

            # Check we have not exceeded cut-off time
            if cut_off_time is not None and time > cut_off_time:
                continue

            # Read three columns of data
            times.append(time)
            fluxes.append(flux)
            flags.append(flag)
            uncertainties.append(uncertainty)

    # Convert into a Lightcurve object
    lightcurve = LightcurveArbitraryRaster(times=np.asarray(times),  # days
                                           fluxes=np.asarray(fluxes),
                                           uncertainties=np.asarray(uncertainties),
                                           flags=np.asarray(flags),
                                           metadata=metadata
                                           )

    # Return lightcurve
    return lightcurve
