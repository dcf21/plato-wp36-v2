# -*- coding: utf-8 -*-
# settings.py

"""
Compile the settings to be used for this installation of the EAS pipeline code. We merge default values for each
setting below with local overrides which can be placed in the YAML file
<configuration/installation_settings.conf>.
"""

import glob
import logging
import os
import re
import sys


class Settings:
    """
    Class containing EAS pipeline settings.
    """

    def __init__(self):
        # Fetch path to local installation settings file
        our_path = os.path.abspath(__file__)
        root_path = re.match(r"(.*)/python_modules/", our_path).group(1)

        self.installation_info = self.fetch_local_settings(root_path=root_path)
        self.settings = self.fetch_environment_settings(root_path=root_path)

    @staticmethod
    def fetch_local_settings(root_path: str):
        # Start building output data structure
        installation_info = {}

        # Sources containing local settings. Later entries override settings in earlier files.
        local_settings_files = []

        for item in glob.glob(os.path.join(root_path, "configuration/*.conf")):
            local_settings_files.append((item, True))

        # Add all local configuration files
        for item in glob.glob(os.path.join(root_path, "../../data/datadir_local/local_settings*.conf")):
            local_settings_files.append((item, False))

        # Read each settings file in turn
        for file_path, must_exist in local_settings_files:
            if not os.path.exists(os.path.join(root_path, file_path)):
                if must_exist:
                    logging.error("You must create a file <{}> with local settings.".format(file_path))
                    sys.exit(1)
                else:
                    continue

            # Read the local installation information from <configuration/installation_settings.conf>
            for line in open(os.path.join(root_path, file_path)):
                line = line.strip()

                # Ignore blank lines and comment lines
                if len(line) == 0 or line[0] == '#':
                    continue

                # Remove any comments from the ends of lines
                if '#' in line:
                    line = line.split('#')[0]

                # Split this configuration parameter into the setting name, and the setting value
                words = line.split(':')
                value = words[1].strip()

                # Try and convert the value of this setting to a float
                try:
                    value = float(value)
                except ValueError:
                    pass

                installation_info[words[0].strip()] = value

        return installation_info

    def fetch_environment_settings(self, root_path: str):
        # The path to the <datadir> directory which is shared between Docker containers, used to store both input
        # and output data from the pipeline
        data_directory = os.path.join(root_path, "../../data/datadir_output")

        # The path to the directory which contains input lightcurves
        lc_directory = os.path.join(root_path, "../../data/datadir_input")

        # The path to the directory which contains input data such as PSLS's frequency data
        input_directory = os.path.join(root_path, "../../data/datadir_input")

        # The path to the directory which contains local installation
        locals_directory = os.path.join(root_path, "../../data/datadir_local")

        # The default settings are below
        settings = {
            'softwareVersion': 1,

            # The path to python scripts in the src directory
            'pythonPath': root_path,

            # The directory where we can store persistent data
            'dataPath': data_directory,

            # The directory where we expect to find input data
            'inDataPath': input_directory,

            # The directory where we expect to find input data
            'localDataPath': locals_directory,

            # The directory where we expect to find lightcurves to work on
            'lcPath': lc_directory,

            # Flag specifying whether to produce debugging output from C code
            'debug': self.installation_info['debug'],
        }

        # If the <datadir> directories aren't mounted properly, then things will be badly wrong, as the Docker container
        # can't access persistent data volumes.
        assert os.path.exists(settings['dataPath']), """
                You need to create a directories or symlinks <datadir_input> and <datadir_output> in the root of your
                working copy of the pipeline, where we store all persistent data.
                """

        return settings
