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

import numpy as np

from typing import Dict, Optional


class Lightcurve:
    """
    A class representing a lightcurve.
    """

    def __init__(self, metadata):
        """
        Create a lightcurve.
        """

        # Make an empty metadata dictionary if none was specified
        if metadata is not None:
            assert isinstance(metadata, dict)
        else:
            metadata = {}

        # Store the data
        self.metadata: dict = metadata
        self.flags_set = False

    def get_time_of_point(self, index: int):
        """
        Return the time associated with a particular data point in the lightcurve [days]
        """
        raise NotImplementedError

    def duration(self):
        """
        Return the duration of the lightcurve [days]
        """
        times = self.get_times()
        duration = times[-1] - times[0]
        return duration

    def get_times(self):
        """
        Return an array of the times of the lightcurve samples [days]
        """
        raise NotImplementedError

    def get_fluxes(self):
        """
        Return an array of the fluxes of the lightcurve samples
        """
        raise NotImplementedError

    def get_uncertainties(self):
        """
        Return an array of the uncertainties of the lightcurve samples
        """
        raise NotImplementedError

    def get_flags(self):
        """
        Return an array of the flags of the lightcurve samples
        """
        raise NotImplementedError

    def to_file(self, target_path: str, binary: bool = False, gzipped: bool = True):
        """
        Write a lightcurve out to a text data file. The time axis is multiplied by a factor 86400 to convert
        from days into seconds.

        :param target_path:
            The target file path where we should create a file representing this lightcurve.
        :param binary:
            Boolean specifying whether we store lightcurve on disk in binary format or plain text.
        :param gzipped:
            Boolean specifying whether we gzip plain-text lightcurves.
        :return:
            Dict of metadata associated with the written file.
        """

        # Pick the writer for this lightcurve
        if not gzipped:
            opener = open
        else:
            opener = gzip.open

        # Write this lightcurve output into lightcurve archive (store times in seconds)
        output = np.transpose([self.get_times() * 86400, self.get_fluxes(), self.get_flags(), self.get_uncertainties()])
        if not binary:
            with opener(target_path, "wt") as out:
                # Output the lightcurve itself
                np.savetxt(out, output)
        else:
            np.save(target_path, output)

        # Metadata associated with this file
        file_metadata = {
            'binary': binary,
            'gzipped': gzipped
        }

        return file_metadata

    def __add__(self, other: Lightcurve):
        """
        Add two lightcurves together.

        :type other:
            Lightcurve
        """
        raise NotImplementedError

    def __sub__(self, other: Lightcurve):
        """
        Subtract one lightcurve from another.

        :type other:
            Lightcurve
        """
        raise NotImplementedError

    def __mul__(self, other: Lightcurve):
        """
        Multiply two lightcurves together.

        :type other:
            Lightcurve
        """
        raise NotImplementedError

    def estimate_sampling_interval(self):
        """
        Estimate the time step on which this light curve is sampled, with robustness against missing points [days]

        :return:
            Time step
        """
        raise NotImplementedError

    def truncate_to_length(self, maximum_time: float, minimum_time: float = 0):
        """
        Truncate a lightcurve to only contain data points within a certain time range [days]

        :param minimum_time:
            The lowest time value for which flux points should be included [days]
        :param maximum_time:
            The highest time value for which flux points should be included [days]
        :return:
            A new Lightcurve object.
        """
        raise NotImplementedError

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
        raise NotImplementedError


class LightcurveArbitraryRaster(Lightcurve):
    """
    A class representing a lightcurve which is sampled on an arbitrary raster of times.
    """

    def __init__(self, times: np.ndarray, fluxes: np.ndarray, uncertainties: Optional[np.ndarray] = None,
                 flags: Optional[np.ndarray] = None, metadata: Dict = None):
        """
        Create a lightcurve.

        :param times:
            Time points [days]
        :param fluxes:
            Flux points [arbitrary units]
        :param uncertainties:
            Uncertainty in each flux point
        :param flags:
            Flags for each data point - 0 means good data; 1 means bad data
        :param metadata:
            The metadata associated with this lightcurve.
        """

        # Call parent class creator method
        super().__init__(metadata=metadata)

        # Check inputs
        assert isinstance(times, np.ndarray)
        assert isinstance(fluxes, np.ndarray)

        # Unset all flags if none were specified
        if flags is not None:
            assert isinstance(flags, np.ndarray)
        else:
            flags = np.zeros_like(times)

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

    def get_time_of_point(self, index: int):
        """
        Return the time associated with a particular data point in the lightcurve [days]
        """
        if index < 0 or index >= len(self.times):
            return np.nan
        else:
            return self.times[index]

    def get_times(self):
        """
        Return an array of the times of the lightcurve samples [days]
        """
        return self.times

    def get_fluxes(self):
        """
        Return an array of the fluxes of the lightcurve samples
        """
        return self.fluxes

    def get_uncertainties(self):
        """
        Return an array of the uncertainties of the lightcurve samples
        """
        return self.uncertainties

    def get_flags(self):
        """
        Return an array of the flags of the lightcurve samples
        """
        return self.fluxes

    @classmethod
    def from_file(cls, file_path: str, file_metadata: Dict, cut_off_time: Optional[float] = None):
        """
        Read a lightcurve from a data file in our lightcurve archive.

        :param file_path:
            The path to the input data file.
        :param file_metadata:
            A dictionary of metadata associated with the input file.
        :param cut_off_time:
            Only read lightcurve up to some cut-off time.
        :return:
            A <LightcurveArbitraryRaster> object.
        """

        # Read file format of lightcurve from metadata
        assert 'binary' in file_metadata
        binary = bool(file_metadata['binary'].value)
        assert 'gzipped' in file_metadata
        gzipped = bool(file_metadata['gzipped'].value)

        # Initialise structures to hold lightcurve data
        times = []  # Times stored as days, but data files contain seconds
        fluxes = []
        uncertainties = []
        flags = []

        if binary:
            # Read binary lightcurve file
            time, flux, flag, uncertainties = np.load(file_path)
            time /= 86400  # Times stored in seconds; but Lightcurve objects use days
        else:
            # Textual lightcurve: loop over lines of input file
            if gzipped:
                file = gzip.open(file_path, "rt")
            else:
                file = open(file_path, "rt")

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
        lightcurve = cls(times=np.asarray(times),
                         fluxes=np.asarray(fluxes),
                         uncertainties=np.asarray(uncertainties),
                         flags=np.asarray(flags),
                         metadata=file_metadata
                         )

        # Return lightcurve
        return lightcurve

    def __add__(self, other: Lightcurve):
        """
        Add two lightcurves together.

        :type other:
            Lightcurve
        """

        # Avoid circular import
        from .lightcurve_resample import LightcurveResampler

        # Resample other lightcurve onto same time raster as this
        resampler = LightcurveResampler(input_lc=other)
        other_resampled = resampler.match_to_other_lightcurve(other=self)

        # Take metadata from the lightcurve with the strongest transit signal
        if self.metadata.get('mes', 1e-20) > other.metadata.get('mes', 0):
            output_metadata = {**self.metadata}
        else:
            output_metadata = {**other.metadata}

        # Create output lightcurve
        result = LightcurveArbitraryRaster(
            times=self.get_times(),
            fluxes=self.get_fluxes() + other_resampled.get_fluxes(),
            uncertainties=np.hypot(self.get_uncertainties(), other_resampled.get_uncertainties()),
            flags=np.hypot(self.get_flags(), other_resampled.get_flags()),
            metadata=output_metadata
        )

        return result

    def __sub__(self, other: Lightcurve):
        """
        Subtract one lightcurve from another.

        :type other:
            Lightcurve
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
            times=self.get_times(),
            fluxes=self.get_fluxes() - other_resampled.get_fluxes(),
            uncertainties=np.hypot(self.get_uncertainties(), other_resampled.get_uncertainties()),
            flags=np.hypot(self.get_flags(), other_resampled.get_flags()),
            metadata=output_metadata
        )

        return result

    def __mul__(self, other: Lightcurve):
        """
        Multiply two lightcurves together.

        :type other:
            Lightcurve
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
            times=self.get_times()[1:-1],
            fluxes=(self.get_fluxes() * other_resampled.get_fluxes())[1:-1],
            uncertainties=np.hypot(self.get_uncertainties(), other_resampled.get_uncertainties())[1:-1],
            flags=np.hypot(self.get_flags(), other_resampled.get_flags())[1:-1],
            metadata=output_metadata
        )

        return result

    def estimate_sampling_interval(self):
        """
        Estimate the time step on which this light curve is sampled, with robustness against missing points [days]

        :return:
            Time step
        """

        # Calculate the inter-quartile mean of the time spacing between samples. This excludes anomalous gaps.
        differences = np.diff(self.times)
        differences_sorted = np.sort(differences)

        interquartile_range_start = int(len(differences) * 0.25)
        interquartile_range_end = int(len(differences) * 0.75)
        interquartile_data = differences_sorted[interquartile_range_start:interquartile_range_end]

        interquartile_mean = np.mean(interquartile_data)

        # Round time interval to nearest number of integer seconds
        interquartile_mean = round(interquartile_mean * 86400) / 86400

        return float(interquartile_mean)

    def truncate_to_length(self, maximum_time: float, minimum_time: float = 0):
        """
        Truncate a lightcurve to only contain data points within a certain time range [days]

        :param minimum_time:
            The lowest time value for which flux points should be included [days]
        :param maximum_time:
            The highest time value for which flux points should be included [days]
        :return:
            A new Lightcurve object.
        """

        times = self.get_times()
        mask = (times >= minimum_time) * (times < maximum_time)

        return LightcurveArbitraryRaster(
            times=times[mask],
            fluxes=self.get_fluxes()[mask],
            uncertainties=self.get_uncertainties()[mask],
            flags=self.get_flags()[mask],
            metadata=self.metadata
        )

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

        spacing = self.estimate_sampling_interval()

        if verbose:
            logging.info("Time step is {:.15f} days".format(spacing))

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
            logging.info("Time step is {:.15f} days".format(spacing))

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


class LightcurveFixedStep(Lightcurve):
    """
    A class representing a lightcurve which is sampled on a fixed time step.
    """

    def __init__(self, time_start: float, time_step: float, fluxes: np.ndarray,
                 uncertainties: Optional[np.ndarray] = None, flags: Optional[np.ndarray] = None,
                 metadata: Optional[Dict] = None):
        """
        Create a lightcurve which is sampled on an arbitrary raster of times.

        :param time_start:
            The time at the start of the lightcurve [days]
        :param time_step:
            The interval between the points in the lightcurve [days]
        :param fluxes:
            Flux points [arbitrary units]
        :param uncertainties:
            Uncertainty in each flux point
        :param flags:
            Flags for each data point - 0 means good data; 1 means bad data
        :param metadata:
            The metadata associated with this lightcurve.
        """

        # Call creator method of the parent class
        super().__init__(metadata=metadata)

        # Check inputs
        assert isinstance(fluxes, np.ndarray)

        # Unset all flags if none were specified
        if flags is not None:
            assert isinstance(flags, np.ndarray)
            flags_set = True
        else:
            flags = np.zeros_like(fluxes)
            flags_set = False

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
        self.flags_set = flags_set
        self.metadata = metadata

    def get_time_of_point(self, index: int):
        """
        Return the time value associated with a particular index in this lightcurve [days]

        :param index:
            The index of the time point within the lightcurve
        :return:
            The time value, in days
        """

        return self.time_start + index * self.time_step

    def get_times(self):
        """
        Return an array of the times of the lightcurve samples [days]
        """
        length = len(self.fluxes)
        return np.linspace(start=self.time_start, num=length, stop=self.time_start + (length + 0.1) * self.time_step)

    def get_fluxes(self):
        """
        Return an array of the fluxes of the lightcurve samples
        """
        return self.fluxes

    def get_uncertainties(self):
        """
        Return an array of the uncertainties of the lightcurve samples
        """
        return self.uncertainties

    def get_flags(self):
        """
        Return an array of the flags of the lightcurve samples
        """
        return self.fluxes

    def estimate_sampling_interval(self):
        """
        Estimate the time step on which this light curve is sampled, with robustness against missing points [days]

        :return:
            Time step
        """
        return self.time_step

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
        return 0

    def truncate_to_length(self, maximum_time: float, minimum_time: float = 0):
        """
        Truncate a lightcurve to only contain data points within a certain time range [days]

        :param minimum_time:
            The lowest time value for which flux points should be included [days]
        :param maximum_time:
            The highest time value for which flux points should be included [days]
        :return:
            A new Lightcurve object.
        """

        times = self.get_times()
        mask = (times >= minimum_time) * (times < maximum_time)

        return LightcurveFixedStep(
            time_start=times[mask][0],
            time_step=self.time_step,
            fluxes=self.get_fluxes()[mask],
            uncertainties=self.get_uncertainties()[mask],
            flags=self.get_flags()[mask],
            metadata=self.metadata
        )

    def __add__(self, other: Lightcurve):
        """
        Add two lightcurves together.

        :type other:
            Lightcurve
        """

        # Avoid circular import
        from .lightcurve_resample import LightcurveResampler

        # Resample other lightcurve onto same time raster as this
        resampler = LightcurveResampler(input_lc=other)
        other_resampled = resampler.match_to_other_lightcurve(other=self)

        # Take metadata from the lightcurve with the strongest transit signal
        if self.metadata.get('mes', 1e-20) > other.metadata.get('mes', 0):
            output_metadata = {**self.metadata}
        else:
            output_metadata = {**other.metadata}

        # Create output lightcurve
        result = LightcurveFixedStep(
            time_start=self.time_start,
            time_step=self.time_step,
            fluxes=self.get_fluxes() + other_resampled.get_fluxes(),
            uncertainties=np.hypot(self.get_uncertainties(), other_resampled.get_uncertainties()),
            flags=np.hypot(self.get_flags(), other_resampled.get_flags()),
            metadata=output_metadata
        )

        return result

    def __sub__(self, other: Lightcurve):
        """
        Subtract one lightcurve from another.

        :type other:
            Lightcurve
        """

        # Avoid circular import
        from .lightcurve_resample import LightcurveResampler

        # Resample other lightcurve onto same time raster as this
        resampler = LightcurveResampler(input_lc=other)
        other_resampled = resampler.match_to_other_lightcurve(other=self)

        # Merge metadata from the two input lightcurves
        output_metadata = {**self.metadata, **other.metadata}

        # Create output lightcurve
        result = LightcurveFixedStep(
            time_start=self.time_start,
            time_step=self.time_step,
            fluxes=self.get_fluxes() - other_resampled.get_fluxes(),
            uncertainties=np.hypot(self.get_uncertainties(), other_resampled.get_uncertainties()),
            flags=np.hypot(self.get_flags(), other_resampled.get_flags()),
            metadata=output_metadata
        )

        return result

    def __mul__(self, other: Lightcurve):
        """
        Multiply two lightcurves together.

        :type other:
            Lightcurve
        """

        # Avoid circular import
        from .lightcurve_resample import LightcurveResampler

        # Resample other lightcurve onto same time raster as this
        resampler = LightcurveResampler(input_lc=other)
        other_resampled = resampler.match_to_other_lightcurve(other=self)

        # Merge metadata from the two input lightcurves
        output_metadata = {**self.metadata, **other.metadata}

        # Create output lightcurve
        result = LightcurveFixedStep(
            time_start=self.time_start,
            time_step=self.time_step,
            fluxes=self.get_fluxes() * other_resampled.get_fluxes(),
            uncertainties=np.hypot(self.get_uncertainties(), other_resampled.get_uncertainties()),
            flags=np.hypot(self.get_flags(), other_resampled.get_flags()),
            metadata=output_metadata
        )

        return result
