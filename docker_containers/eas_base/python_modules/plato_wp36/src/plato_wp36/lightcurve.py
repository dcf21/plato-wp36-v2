# -*- coding: utf-8 -*-
# lightcurve.py

"""
Classes for representing light curves, either on arbitrary time rasters, or on rasters with fixed step.
"""

# This allows class methods to type-hint their arguments as being class instances, before the class is fully defined
from __future__ import annotations

import gzip
import logging
import math
import os

import numpy as np

from typing import Dict, Optional

from .task_database import TaskDatabaseConnection


class LightcurveArbitraryRaster:
    """
    A class representing a lightcurve which is sampled on an arbitrary raster of times.
    """

    def __init__(self, times: np.ndarray, fluxes: np.ndarray, uncertainties: Optional[np.ndarray] = None,
                 flags: Optional[np.ndarray] = None, metadata: Dict = None):
        """
        Create a lightcurve which is sampled on an arbitrary raster of times.

        :param times:
            The times of the data points (days).
        :param fluxes:
            The light fluxes at each data point.
        :param uncertainties:
            The uncertainty in each data point.
        :param flags:
            The flag associated with each data point.
        :param metadata:
            The metadata associated with this lightcurve.
        """

        # Check inputs
        assert isinstance(times, np.ndarray)
        assert isinstance(fluxes, np.ndarray)

        # Unset all flags if none were specified
        if flags is not None:
            assert isinstance(flags, np.ndarray)
        else:
            flags = np.zeros_like(times)

        # Make an empty metadata dictionary if none was specified
        if metadata is not None:
            assert isinstance(metadata, dict)
        else:
            metadata = {}

        # Make uncertainty zero if not specified
        if uncertainties is not None:
            assert isinstance(uncertainties, np.ndarray)
        else:
            uncertainties = np.zeros_like(fluxes)

        # Store the data
        self.times: np.ndarray = times  # days
        self.fluxes: np.ndarray = fluxes
        self.uncertainties: np.ndarray = uncertainties
        self.flags: np.ndarray = flags
        self.flags_set: bool = True
        self.metadata: dict = metadata

    def to_file(self, directory: str, filename: str, execution_id: int,
                binary: bool = False, gzipped: bool = True):
        """
        Write a lightcurve out to a text data file. The time axis is multiplied by a factor 86400 to convert
        from days into seconds.

        :param filename:
            The filename of the lightcurve (within our local lightcurve archive).
        :param directory:
            The name of the directory inside the lightcurve archive where this lightcurve should be saved.
        :param execution_id:
            The integer ID of the task execution attempt id generating this file.
        :param binary:
            Boolean specifying whether we store lightcurve on disk in binary format or plain text.
        :param gzipped:
            Boolean specifying whether we gzip plain-text lightcurves.
        """

        # Open a connection to the task database
        task_db = TaskDatabaseConnection()

        # Create temporary working directory
        identifier = "eas_lc_writer"
        id_string = "eas_{:d}_{}".format(os.getpid(), identifier)
        tmp_dir = os.path.join("/tmp", id_string)
        os.makedirs(name=tmp_dir, mode=0o700, exist_ok=True)

        # Target path for this lightcurve
        target_path = os.path.join(tmp_dir, filename)

        # Pick the writer for this lightcurve
        if not gzipped:
            opener = open
        else:
            opener = gzip.open

        # Write this lightcurve output into lightcurve archive (store times in seconds)
        if not binary:
            with opener(target_path, "wt") as out:
                # Output the lightcurve itself
                np.savetxt(out, np.transpose([self.times * 86400, self.fluxes, self.flags, self.uncertainties]))
        else:
            np.save(target_path, np.transpose([self.times * 86400, self.fluxes, self.flags, self.uncertainties]))

        # Find out what file product this lightcurve corresponds to
        product_ids = task_db.file_product_by_filename(directory=directory, filename=filename)
        assert len(product_ids) > 0, \
            ("This lightcurve <{}/{}> does not correspond to any file product in the database".
             format(directory, filename))
        product_id = product_ids[0]

        # Import lightcurve into the task database
        task_db.file_version_register(product_id=product_id, generated_by_task_execution=execution_id,
                                      file_path_input=target_path, preserve=False, metadata=self.metadata)

        # Close database
        task_db.commit()
        task_db.close_db()

        # Clean up temporary directory
        os.rmdir(tmp_dir)

    @classmethod
    def from_file(cls, directory: str, filename: str,
                  cut_off_time: Optional[float] = None,
                  execution_id: Optional[int] = None, must_have_passed_qc: bool = True):
        """
        Read a lightcurve from a data file in our lightcurve archive.

        :param filename:
            The filename of the input data file.
        :param cut_off_time:
            Only read lightcurve up to some cut off time
        :param directory:
            The directory in which the lightcurve is stored.
        :param execution_id:
            The ID number of the task execution attempt which generated this file product. If None, then
            we open the latest-dated version of this file product.
        :param must_have_passed_qc:
            Boolean flag indicating whether this lightcurve must have passed QC for us to be allowed to open it.
        :return:
            A <LightcurveArbitraryRaster> object.
        """

        # Open a connection to the task database
        task_db = TaskDatabaseConnection()

        # Find out what file product this lightcurve corresponds to
        product_ids = task_db.file_product_by_filename(directory=directory, filename=filename)
        assert len(product_ids) > 0, \
            ("This lightcurve <{}/{}> does not correspond to any file product in the database".
             format(directory, filename))
        product_id = product_ids[0]

        # Find out which version of this file we should use
        version_ids = task_db.file_version_by_product(product_id=product_id, attempt_id=execution_id,
                                                      must_have_passed_qc=must_have_passed_qc)
        assert len(version_ids) > 0, \
            ("No matching lightcurve <{}/{}> found in the database".
             format(execution_id, product_id))
        version_id = version_ids[-1]

        # Fetch file product version record
        file_info = task_db.file_version_lookup(product_version_id=version_id)
        file_location = task_db.file_version_path_for_id(product_version_id=version_id, full_path=True)

        # Read file format of lightcurve from metadata
        assert 'binary' in file_info.metadata
        binary = bool(file_info.metadata['binary'])
        assert 'gzipped' in file_info.metadata
        gzipped = bool(file_info.metadata['gzipped'])

        # Initialise structures to hold lightcurve data
        times = []  # Times stored as days, but data files contain seconds
        fluxes = []
        uncertainties = []
        flags = []

        # Look up file open function
        file_opener = gzip.open if gzipped else open

        if binary:
            # Read binary lightcurve file
            time, flux, flag, uncertainties = np.load(file_location)
            time /= 86400  # Times stored in seconds; but Lightcurve objects use days
        else:
            # Textual lightcurve: loop over lines of input file
            with file_opener(file_location, "rt") as file:
                for line in file:
                    # Ignore blank lines and comment lines
                    if len(line) == 0 or line[0] == '#':
                        continue

                    # Unpack data
                    words = line.split()
                    time = float(words[0]) / 86400  # Times stored on disk in seconds; but Lightcurve objects use days
                    flux = float(words[1])
                    flag = float(words[2])
                    uncertainty = float(words[3])

                    # Check we have not exceeded cut-off time
                    if cut_off_time is not None and time > cut_off_time:
                        continue

                    # Read three columns of data
                    times.append(time)
                    fluxes.append(flux)
                    flags.append(flag)
                    uncertainties.append(uncertainty)

        # Convert into a Lightcurve object
        lightcurve = LightcurveArbitraryRaster(times=np.asarray(times),
                                               fluxes=np.asarray(fluxes),
                                               uncertainties=np.asarray(uncertainties),
                                               flags=np.asarray(flags),
                                               metadata=file_info.metadata
                                               )

        # Return lightcurve
        return lightcurve

    def __add__(self, other: LightcurveArbitraryRaster):
        """
        Add two lightcurves together.

        :type other:
            LightcurveArbitraryRaster
        """

        # Avoid circular import
        from .lightcurve_resample import LightcurveResampler

        # Resample other lightcurve onto same time raster as this
        resampler = LightcurveResampler(input_lc=other)
        other_resampled = resampler.match_to_other_lightcurve(other=self)

        # Take metadata from the lightcurve with the strongest transit signal
        if self.metadata['mes'] > other.metadata['mes']:
            output_metadata = {**self.metadata}
        else:
            output_metadata = {**other.metadata}

        # Create output lightcurve
        result = LightcurveArbitraryRaster(
            times=self.times,
            fluxes=self.fluxes + other_resampled.fluxes,
            uncertainties=np.hypot(self.uncertainties, other_resampled.uncertainties),
            flags=np.hypot(self.flags, other_resampled.flags),
            metadata=output_metadata
        )

        return result

    def __sub__(self, other: LightcurveArbitraryRaster):
        """
        Subtract one lightcurve from another.

        :type other:
            LightcurveArbitraryRaster
        """

        # Avoid circular import
        from .lightcurve_resample import LightcurveResampler

        # Resample other lightcurve onto same time raster as this
        resampler = LightcurveResampler(input_lc=other)
        other_resampled = resampler.match_to_other_lightcurve(other=self)

        # Merge metadata from the two input lightcurves
        output_metadata = {**self.metadata, **other.metadata}

        # Create output lightcurve
        result = LightcurveArbitraryRaster(
            times=self.times,
            fluxes=self.fluxes - other_resampled.fluxes,
            uncertainties=np.hypot(self.uncertainties, other_resampled.uncertainties),
            flags=np.hypot(self.flags, other_resampled.flags),
            metadata=output_metadata
        )

        return result

    def __mul__(self, other: LightcurveArbitraryRaster):
        """
        Multiply two lightcurves together.

        :type other:
            LightcurveArbitraryRaster
        """

        # Avoid circular import
        from .lightcurve_resample import LightcurveResampler

        # Resample other lightcurve onto same time raster as this
        resampler = LightcurveResampler(input_lc=other)
        other_resampled = resampler.match_to_other_lightcurve(other=self)

        # Merge metadata from the two input lightcurves
        output_metadata = {**self.metadata, **other.metadata}

        # Create output lightcurve. Remove first and last data points due to edge effects
        result = LightcurveArbitraryRaster(
            times=self.times[1:-1],
            fluxes=(self.fluxes * other_resampled.fluxes)[1:-1],
            uncertainties=np.hypot(self.uncertainties, other_resampled.uncertainties)[1:-1],
            flags=np.hypot(self.flags, other_resampled.flags)[1:-1],
            metadata=output_metadata
        )

        return result

    def estimate_sampling_interval(self):
        """
        Estimate the time step on which this light curve is sampled, with robustness against missing points.

        :return:
            Time step
        """

        differences = np.diff(self.times)
        differences_sorted = np.sort(differences)

        interquartile_range_start = int(len(differences) * 0.25)
        interquartile_range_end = int(len(differences) * 0.75)
        interquartile_data = differences_sorted[interquartile_range_start:interquartile_range_end]

        interquartile_mean = np.mean(interquartile_data)

        # Round time interval to nearest number of integer seconds
        interquartile_mean = round(interquartile_mean * 86400) / 86400

        return float(interquartile_mean)

    def check_fixed_step(self, verbose: bool = True, max_errors: int = 6):
        """
        Check that this light curve is sampled at a fixed time interval. Return the number of errors.

        :param verbose:
            Should we output a logging message about every missing time point?
        :param max_errors:
            The maximum number of errors we should show
        :return:
            int
        """

        abs_tol = 1e-4
        rel_tol = 0

        error_count = 0
        spacing = self.estimate_sampling_interval()

        if verbose:
            logging.info("Time step is {:.15f}".format(spacing))

        differences = np.diff(self.times)

        for index, step in enumerate(differences):
            # If this time point has the correct spacing, it is OK
            if math.isclose(step, spacing, abs_tol=abs_tol, rel_tol=rel_tol):
                continue

            # We have found a problem
            error_count += 1

            # See if we have skipped some time points
            points_missed = step / spacing - 1
            if math.isclose(points_missed, round(points_missed), abs_tol=abs_tol, rel_tol=rel_tol):
                if verbose and (max_errors is None or error_count <= max_errors):
                    logging.info("index {:5d} - {:d} points missing at time {:.5f}".format(index,
                                                                                           int(points_missed),
                                                                                           self.times[index]))
                continue

            # Or is this an entirely unexpected time interval?
            if verbose and (max_errors is None or error_count <= max_errors):
                logging.info("index {:5d} - Unexpected time step {:.15f} at time {:.5f}".format(index,
                                                                                                step,
                                                                                                self.times[index]))

        # Return total error count
        if verbose and error_count > 0:
            logging.info("Lightcurve had gaps at {}/{} time points.".format(error_count, len(self.times)))

        # Return the verdict on this lightcurve
        return error_count

    def check_fixed_step_v2(self, verbose: bool = True, max_errors: int = 6):
        """
        Check that this light curve is sampled at a fixed time interval. Return the number of errors.

        :param verbose:
            Should we output a logging message about every missing time point?
        :param max_errors:
            The maximum number of errors we should show
        :return:
            int
        """

        abs_tol = 1e-4
        rel_tol = 0

        spacing = self.estimate_sampling_interval()

        if verbose:
            logging.info("Time step is {:.15f}".format(spacing))

        start_time = self.times[0]
        end_time = self.times[-1]
        times = np.arange(start=start_time, stop=end_time, step=spacing)
        error_count = 0

        input_position = 0
        for index, time in enumerate(times):
            closest_time_point = self.times[input_position]
            while ((not math.isclose(time, self.times[input_position], abs_tol=abs_tol, rel_tol=rel_tol)) and
                   (time > self.times[input_position])):
                if abs(self.times[input_position] - time) < abs(closest_time_point - time):
                    closest_time_point = self.times[input_position]
                input_position += 1

            # If this time point has the correct spacing, it is OK
            if not math.isclose(time, self.times[input_position], abs_tol=abs_tol, rel_tol=rel_tol):
                if abs(self.times[input_position] - time) < abs(closest_time_point - time):
                    closest_time_point = self.times[input_position]
                if verbose and (max_errors is None or error_count <= max_errors):
                    logging.info("index {:5d} - Point missing at time {:.15f}. Closest time was {:.15f}.".
                                 format(index, self.times[index], closest_time_point))
                error_count += 1

        # Return total error count
        if verbose and error_count > 0:
            logging.info("Lightcurve had gaps at {}/{} time points.".format(error_count, len(self.times)))

        # Return the verdict on this lightcurve
        return error_count

    def to_fixed_step(self, verbose: bool = True, max_errors: int = 6):
        """
        Convert this lightcurve to a fixed time stride.

        :param verbose:
            Should we output a logging message about every missing time point?
        :param max_errors:
            The maximum number of errors we should show
        :return:
            [LightcurveFixedStep]
        """

        abs_tol = 1e-4
        rel_tol = 0

        spacing = self.estimate_sampling_interval()

        if verbose:
            logging.info("Time step is {:.15f}".format(spacing))

        start_time = self.times[0]
        end_time = self.times[-1]
        times = np.arange(start=start_time, stop=end_time, step=spacing)
        output = np.zeros_like(times)
        error_count = 0

        # Iterate over each time point in the fixed-step output lightcurve
        input_position = 0
        for index, time in enumerate(times):
            # Find the time point in the input lightcurve which is closest to this time
            closest_time_point = [self.times[input_position], self.fluxes[input_position]]
            while ((not math.isclose(time, self.times[input_position], abs_tol=abs_tol, rel_tol=rel_tol))
                   and (time > self.times[input_position])):
                if abs(self.times[input_position] - time) < abs(closest_time_point[0] - time):
                    closest_time_point = [self.times[input_position], self.fluxes[input_position]]
                input_position += 1

            if abs(self.times[input_position] - time) < abs(closest_time_point[0] - time):
                closest_time_point = [self.times[input_position], self.fluxes[input_position]]

            # If this time point has the correct spacing, it is OK
            if math.isclose(time, self.times[input_position], abs_tol=abs_tol, rel_tol=rel_tol):
                output[index] = closest_time_point[1]
                continue

            if verbose and (max_errors is None or error_count <= max_errors):
                logging.info("index {:5d} - Point missing at time {:.15f}. Closest time was {:.15f}.".
                             format(index, self.times[index], closest_time_point[0]))
            error_count += 1
            output[index] = 1

        # Return total error count
        if verbose and error_count > 0:
            logging.info("Lightcurve had gaps at {}/{} time points.".format(error_count, len(times)))

        # Return lightcurve
        return LightcurveFixedStep(
            time_start=start_time,
            time_step=spacing,
            fluxes=output
        )


class LightcurveFixedStep:
    """
    A class representing a lightcurve which is sampled on a fixed time step.
    """

    def __init__(self, time_start: float, time_step: float, fluxes: np.ndarray,
                 uncertainties: Optional[np.ndarray] = None, flags: Optional[np.ndarray] = None,
                 metadata: Optional[Dict] = None):
        """
        Create a lightcurve which is sampled on an arbitrary raster of times.

        :param time_start:
            The time at the start of the lightcurve.
        :param time_step:
            The interval between the points in the lightcurve.
        :param fluxes:
            The light fluxes at each data point.
        :param uncertainties:
            The uncertainty in each data point.
        :param flags:
            The flag associated with each data point.
        :param metadata:
            The metadata associated with this lightcurve.
        """

        # Check inputs
        assert isinstance(fluxes, np.ndarray)

        # Unset all flags if none were specified
        if flags is not None:
            assert isinstance(flags, np.ndarray)
        else:
            flags = np.zeros_like(fluxes)

        # Make an empty metadata dictionary if none was specified
        if metadata is not None:
            assert isinstance(metadata, dict)
        else:
            metadata = {}

        # Make uncertainty zero if not specified
        if uncertainties is not None:
            assert isinstance(uncertainties, np.ndarray)
        else:
            uncertainties = np.zeros_like(fluxes)

        # Store the data
        self.time_start = float(time_start)
        self.time_step = float(time_step)
        self.fluxes = fluxes
        self.uncertainties = uncertainties
        self.flags = flags
        self.flags_set = True
        self.metadata = metadata

    def time_value(self, index: float):
        """
        Return the time value associated with a particular index in this lightcurve.

        :param index:
            The index of the time point within the lightcurve
        :return:
            The time value, in days
        """

        return self.time_start + index * self.time_step
