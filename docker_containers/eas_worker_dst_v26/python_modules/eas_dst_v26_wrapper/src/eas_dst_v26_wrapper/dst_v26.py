# -*- coding: utf-8 -*-
# dst_v26.py

import os
import numpy as np
from astropy.io import fits

from plato_wp36.lightcurve import LightcurveArbitraryRaster
from plato_wp36 import settings, task_execution, temporary_directory

from typing import Optional


def process_lightcurve(lc: LightcurveArbitraryRaster, lc_duration: Optional[float], search_settings: dict):
    """
    Perform a transit search on a light curve, using the dst code, version 26.

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

    # Look up EAS pipeline settings
    eas_settings = settings.Settings()

    # Make a temporary directory
    with temporary_directory.TemporaryDirectory() as tmp_dir:
        # Copy DST code into the temporary directory
        dst_input_path = os.path.join(eas_settings.settings['pythonPath'], "private_code")
        dst_working_path = os.path.join(tmp_dir.tmp_dir, "private_code")

        task_execution.call_subprocess_and_log_output(
            arguments=("rsync", "-av", dst_input_path, dst_working_path)
        )

        # Figure out where DST is going to expect to find its input configuration
        fits_file_path = os.path.join(dst_working_path, "k2-3", "DATOS", "DAT", "lc.fits")

        # Keep track of our default working directory
        cwd = os.getcwd()

        # Make working directory structure
        os.chdir(dst_working_path)
        task_execution.call_subprocess_and_log_output(arguments=("./asalto26.5/scripts/hazdir.sh k2-3"))
        os.chdir(cwd)

        # Output LC in FITS format for DST
        col1 = fits.Column(name='T', format='E', array=time)
        col2 = fits.Column(name='CADENCENO', format='E', array=np.arange(len(time)))
        col3 = fits.Column(name='FCOR', format='E', array=flux)
        cols = fits.ColDefs([col1, col2, col3])
        table_hdu = fits.BinTableHDU.from_columns(cols)

        # Populate FITS headers
        hdr = fits.Header()
        hdr['KEPLERID'] = '0'
        hdr['RA'] = '0'
        hdr['DEC'] = '0'
        hdr['KEPMAG'] = '0'
        empty_primary = fits.PrimaryHDU(header=hdr)

        # Output FITS file
        hdul = fits.HDUList([empty_primary, table_hdu])
        hdul.writeto(fits_file_path)

        # Run onyva_k2vanderburg.exe
        os.chdir(dst_working_path)
        task_execution.call_subprocess_and_log_output(
            arguments=("./asalto26.5/bin/onyva_k2vanderburg.exe", "-Rru", ".", "lc.fits")
        )
        os.chdir(cwd)

    # Return nothing for now
    results = {}

    # Extended results to save to disk
    results_extended = results

    # Return results
    return results, results_extended
