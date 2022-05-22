# -*- coding: utf-8 -*-
# psls_wrapper.py

"""
Class for synthesising lightcurves using PSLS.
"""

import glob
import hashlib
import os
import random
import time
from math import asin, pi

from typing import Optional

import numpy as np
from eas_batman_wrapper.batman_wrapper import BatmanWrapper
from plato_wp36 import settings, lightcurve, task_execution, temporary_directory
from plato_wp36.constants import EASConstants


class PslsWrapper:
    """
    Class for synthesising lightcurves using PSLS.
    """

    def __init__(self,
                 mode: Optional[str] = None,
                 duration: Optional[float] = None,
                 t0: Optional[float] = None,
                 enable_transits: Optional[bool] = None,
                 star_radius: Optional[float] = None,
                 planet_radius: Optional[float] = None,
                 orbital_period: Optional[float] = None,
                 semi_major_axis: Optional[float] = None,
                 orbital_angle: Optional[float] = None,
                 impact_parameter: Optional[float] = None,
                 nsr: Optional[float] = None,
                 sampling_cadence: Optional[float] = None,
                 mask_updates: Optional[bool] = None,
                 enable_systematics: Optional[bool] = None,
                 enable_random_noise: Optional[bool] = None,
                 number_camera_groups: Optional[int] = None,
                 number_cameras_per_group: Optional[int] = None
                 ):
        """
        Instantiate wrapper for synthesising lightcurves using PSLS.

        :param mode:
            Either "main_sequence" or "red_giant" to choose between two default star models.
        :param duration:
            Duration of the lightcurve we are to generate (days)
        :param t0:
            Time of inferior conjunction relative to the beginning of the lightcurve (days)
        :param enable_transits:
            Boolean indicating whether we inject transits into this LC.
        :param star_radius:
            The radius of the star (Jupiter radii)
        :param planet_radius:
            The radius of the planet (Jupiter radii)
        :param orbital_period:
            The orbital period of the planet (days)
        :param semi_major_axis:
            The semi-major axis of the exoplanet orbit (AU)
        :param orbital_angle:
            Orbital inclination to the line of sight (degrees). Zero means orbit is perfectly edge-on.
        :param impact_parameter:
            The impact parameter of the exoplanet (0-1). Overrides <orbital_angle> if not None.
        :param nsr:
            The noise-to-signal ratio (ppm/hr). Default value is 73 for nominal PLATO performance.
        :param sampling_cadence:
            The sampling cadence of the lightcurve (seconds)
        :param mask_updates:
            Boolean indicating whether we enable mask updates in PSLS
        :param enable_systematics:
            Boolean indicating whether we enable systematic effects in PSLS.
        :param enable_random_noise:
            Boolean indicating whether we enable random noise.
        :param number_camera_groups:
            The number of camera groups to simulate (1-4)
        :param number_cameras_per_group:
            The number of cameras to simulate in each group (1-6)
        """

        # Look up settings
        self.eas_settings = settings.Settings()
        self.constants = EASConstants()

        # Create dictionary of default settings
        self.settings = {
            'mode': 'main_sequence',
            'duration': 730,  # days
            't0': 1,  # Time for inferior conjunction (days)
            'master_seed': time.time(),
            'datadir_local': self.eas_settings.settings['localDataPath'],
            'enable_transits': True,
            'star_radius': self.constants.sun_radius / self.constants.jupiter_radius,  # Jupiter radii
            'planet_radius': 1,  # Jupiter radii
            'orbital_period': 365,  # days
            'semi_major_axis': 1,  # AU
            'orbital_angle': 0,  # degrees
            'impact_parameter': None,  # Impact parameter (0-1); overrides <orbital_angle> if not None
            'nsr': 73,  # noise-to-signal ratio (ppm/hr)
            'sampling_cadence': 25,  # sampling cadence, seconds
            'mask_updates': False,  # do we include mask updates?
            'enable_systematics': False,  # do we include systematics?
            'enable_random_noise': True,  # do we include random noise?
            'number_camera_groups': 4,  # the number of groups of cameras to simulate
            'number_cameras_per_group': 6  # the number of cameras to simulate in each group
        }

        self.configure(mode=mode, duration=duration, t0=t0, enable_transits=enable_transits,
                       star_radius=star_radius, planet_radius=planet_radius,
                       orbital_period=orbital_period, semi_major_axis=semi_major_axis,
                       orbital_angle=orbital_angle, impact_parameter=impact_parameter,
                       nsr=nsr, sampling_cadence=sampling_cadence, mask_updates=mask_updates,
                       enable_systematics=enable_systematics, enable_random_noise=enable_random_noise,
                       number_camera_groups=number_camera_groups, number_cameras_per_group=number_cameras_per_group)

        # Create temporary working directory
        identifier = "eas_psls"
        self.id_string = "eas_{:d}_{}".format(os.getpid(), identifier)
        self.tmp_dir = temporary_directory.TemporaryDirectory()
        self.active = True

    def __enter__(self):
        """
        Called at the start of a with block
        """
        return self

    def __del__(self):
        """
        Destructor
        """
        self.close()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called at the end of a with block
        """
        self.close()

    def close(self):
        """
        Clean up temporary working data.
        """

        # Remove temporary directory
        if self.tmp_dir is not None:
            self.tmp_dir.clean_up()
            self.tmp_dir = None
        self.active = False

    def configure(self,
                  mode: Optional[str] = None,
                  duration: Optional[float] = None,
                  t0: Optional[float] = None,
                  enable_transits: Optional[bool] = None,
                  star_radius: Optional[float] = None,
                  planet_radius: Optional[float] = None,
                  orbital_period: Optional[float] = None,
                  semi_major_axis: Optional[float] = None,
                  orbital_angle: Optional[float] = None,
                  impact_parameter: Optional[float] = None,
                  nsr: Optional[float] = None,
                  sampling_cadence: Optional[float] = None,
                  mask_updates: Optional[bool] = None,
                  enable_systematics: Optional[bool] = None,
                  enable_random_noise: Optional[bool] = None,
                  number_camera_groups: Optional[int] = None,
                  number_cameras_per_group: Optional[int] = None
                  ):
        """
        Change settings for synthesising lightcurves using PSLS.

        :param mode:
            Either "main_sequence" or "red_giant" to choose between two default star models.
        :param duration:
            Duration of the lightcurve we are to generate (days)
        :param t0:
            Time of inferior conjunction relative to the beginning of the lightcurve (days)
        :param enable_transits:
            Boolean indicating whether we inject transits into this LC.
        :param star_radius:
            The radius of the star (Jupiter radii)
        :param planet_radius:
            The radius of the planet (Jupiter radii)
        :param orbital_period:
            The orbital period of the planet (days)
        :param semi_major_axis:
            The semi-major axis of the exoplanet orbit (AU)
        :param orbital_angle:
            Orbital inclination to the line of sight (degrees). Zero means orbit is perfectly edge-on.
        :param impact_parameter:
            The impact parameter of the exoplanet (0-1). Overrides <orbital_angle> if not None.
        :param nsr:
            The noise-to-signal ratio (ppm/hr). Default value is 73 for nominal PLATO performance.
        :param sampling_cadence:
            The sampling cadence of the lightcurve (seconds)
        :param mask_updates:
            Boolean indicating whether we enable mask updates in PSLS
        :param enable_systematics:
            Boolean indicating whether we enable systematic effects in PSLS.
        :param enable_random_noise:
            Boolean indicating whether we enable random noise.
        :param number_camera_groups:
            The number of camera groups to simulate (1-4)
        :param number_cameras_per_group:
            The number of cameras to simulate in each group (1-6)
        """

        # Create dictionary of settings
        if mode is not None:
            self.settings['mode'] = mode
        if duration is not None:
            self.settings['duration'] = float(duration)
        if t0 is not None:
            self.settings['t0'] = float(t0)
        if enable_transits is not None:
            self.settings['enable_transits'] = int(enable_transits)
        if star_radius is not None:
            self.settings['star_radius'] = float(star_radius)
        if planet_radius is not None:
            self.settings['planet_radius'] = float(planet_radius)
        if orbital_period is not None:
            self.settings['orbital_period'] = float(orbital_period)
        if semi_major_axis is not None:
            self.settings['semi_major_axis'] = float(semi_major_axis)
        if orbital_angle is not None:
            self.settings['orbital_angle'] = float(orbital_angle)
            self.settings['impact_parameter'] = None
        if impact_parameter is not None:
            self.settings['impact_parameter'] = float(impact_parameter)
            self.settings['orbital_angle'] = None
        if nsr is not None:
            self.settings['nsr'] = float(nsr)
        if sampling_cadence is not None:
            self.settings['sampling_cadence'] = float(sampling_cadence)
        if mask_updates is not None:
            self.settings['mask_updates'] = int(mask_updates)
        if enable_systematics is not None:
            self.settings['enable_systematics'] = int(enable_systematics)
        if enable_random_noise is not None:
            self.settings['enable_random_noise'] = int(enable_random_noise)
        if number_camera_groups is not None:
            self.settings['number_camera_groups'] = int(number_camera_groups)
        if number_cameras_per_group is not None:
            self.settings['number_cameras_per_group'] = int(number_cameras_per_group)

    def synthesise(self):
        """
        Synthesise a lightcurve using PSLS
        """

        assert self.active, "This synthesiser instance has been closed."

        # Switch into our temporary working directory where PSLS can find all its input files
        cwd = os.getcwd()
        os.chdir(self.tmp_dir.tmp_dir)

        # Create unique ID for this run
        utc = time.time()
        key = "{}_{}".format(utc, random.random())
        tstr = time.strftime("%Y%m%d_%H%M%S", time.gmtime(utc))
        uid = hashlib.md5(key.encode()).hexdigest()
        run_identifier = "{}_{}".format(tstr, uid)[0:32]

        # Find template to use for PSLS configuration
        path_to_yaml_templates = os.path.split(os.path.abspath(__file__))[0]
        yaml_template_filename = os.path.join(path_to_yaml_templates, "{}_template.yaml".format(self.settings['mode']))

        assert os.path.exists(yaml_template_filename), \
            """Could not find PSLS template for mode <{}>. Recognised modes are "main_sequence" or "red_giant".\
               File <{}> does not exist.\
            """.format(self.settings['mode'], yaml_template_filename)

        # Make filename for YAML configuration file for PSLS
        yaml_template = open(yaml_template_filename).read()
        yaml_filename = "{}.yaml".format(run_identifier)

        # Work out inclination of orbit, which may be specified either as an inclination to the line of sight (degrees)
        # or as an impact parameter (0-1).
        if self.settings['impact_parameter'] is not None:
            orbital_angle = asin(self.settings['impact_parameter'] * self.settings['star_radius'] /
                                 (self.settings['semi_major_axis'] * (
                                         self.constants.phy_AU / self.constants.jupiter_radius))
                                 ) * 180 / pi
        else:
            orbital_angle = self.settings['orbital_angle']

        # Work out which systematics file we are to use
        systematics_file = ("PLATO_systematics_BOL_V2.npy"
                            if self.settings['mask_updates'] else
                            "PLATO_systematics_BOL_FixedMask_V2.npy")

        enable_systematics = int(self.settings['enable_systematics'])
        enable_random_noise = int(self.settings['enable_random_noise'])
        number_camera_groups = int(self.settings['number_camera_groups'])
        number_cameras_per_group = int(self.settings['number_cameras_per_group'])

        # PSLS always puts first transit at the beginning of the lightcurve, so we create a longer lightcurve
        # and cut out a segment with the first transit in the requested position
        run_in_time = self.settings['orbital_period'] - self.settings['t0']  # days
        simulation_duration = run_in_time + self.settings['duration'] + 1

        # Create YAML configuration file for PSLS
        with open(yaml_filename, "w") as out:
            out.write(
                yaml_template.format(
                    duration=simulation_duration,
                    master_seed=int(self.settings['master_seed']),
                    nsr=float(self.settings['nsr']),
                    datadir_local=self.settings['datadir_local'],
                    enable_transits=int(self.settings['enable_transits']),
                    planet_radius=float(self.settings['planet_radius']),
                    orbital_period=float(self.settings['orbital_period']),
                    semi_major_axis=float(self.settings['semi_major_axis']),
                    orbital_angle=float(orbital_angle),
                    sampling_cadence=float(self.settings['sampling_cadence']),
                    integration_time=float(self.settings['sampling_cadence']) * 22 / 25,
                    systematics=systematics_file,
                    enable_systematics=int(enable_systematics),
                    noise_type="PLATO_SIMU" if enable_systematics else "PLATO_SCALING",
                    enable_random_noise=int(enable_random_noise),
                    number_camera_groups=int(number_camera_groups),
                    number_cameras_per_group=int(number_cameras_per_group)
                )
            )

        # Path to PSLS binary
        psls_binary = os.path.join(self.settings['datadir_local'], "virtualenv/bin/psls.py")

        # Run PSLS
        task_execution.call_subprocess_and_log_output(
            arguments=(psls_binary, yaml_filename)
        )

        # Filename of the output that PSLS produced
        psls_output = "0012069449"

        # Read output from PSLS
        psls_filename = "{}.dat".format(psls_output)
        data = np.loadtxt(psls_filename).T

        # Read times and fluxes from text file
        times = data[0]  # seconds
        fluxes = 1 + 1e-6 * data[1]
        flags = data[2]

        # Cut out the segment we are to return to the user
        cadence_days = self.settings['sampling_cadence'] / 3600. / 24.
        run_in_samples = int(run_in_time / cadence_days)
        final_length = int(self.settings['duration'] / cadence_days)

        times = times[run_in_samples: run_in_samples + final_length]
        fluxes = fluxes[run_in_samples: run_in_samples + final_length]
        flags = flags[run_in_samples: run_in_samples + final_length]

        # Compute MES statistic. To do this, we need a theoretical model of the pure transit signal, which we
        # generate using batman.
        if not self.settings['enable_transits']:
            integrated_transit_power = 0
            pixels_in_transit = 0
            pixels_out_of_transit = len(times)
            mes = 0
        else:
            batman_instance = BatmanWrapper(duration=self.settings['duration'],
                                            eccentricity=0,
                                            t0=self.settings['t0'],
                                            star_radius=self.settings['star_radius'],
                                            planet_radius=self.settings['planet_radius'],
                                            orbital_period=self.settings['orbital_period'],
                                            semi_major_axis=self.settings['semi_major_axis'],
                                            orbital_angle=self.settings['orbital_angle'],
                                            impact_parameter=self.settings['impact_parameter'],
                                            noise=self.constants.plato_noise * (self.settings['nsr'] / 73),
                                            sampling_cadence=self.settings['sampling_cadence']
                                            )
            batman_lc = batman_instance.synthesise()
            integrated_transit_power = batman_lc.metadata['integrated_transit_power']
            pixels_in_transit = batman_lc.metadata['pixels_in_transit']
            pixels_out_of_transit = batman_lc.metadata['pixels_out_of_transit']
            mes = batman_lc.metadata['mes']

        output_metadata = {
            'integrated_transit_power': integrated_transit_power,
            'pixels_in_transit': pixels_in_transit,
            'pixels_out_of_transit': pixels_out_of_transit,
            'mes': mes
        }

        # Write Batman output into lightcurve archive
        lc = lightcurve.LightcurveArbitraryRaster(
            times=times / 86400,  # psls outputs seconds; we use days
            fluxes=fluxes,
            flags=flags,
            metadata={**self.settings, **output_metadata}
        )

        # Make sure there aren't any old data files lying around
        for dead_file in glob.glob("*.modes") + glob.glob("*.yaml") + glob.glob("*.dat"):
            os.unlink(dead_file)

        # Switch back into the user's cwd
        os.chdir(cwd)

        # Finished
        return lc
