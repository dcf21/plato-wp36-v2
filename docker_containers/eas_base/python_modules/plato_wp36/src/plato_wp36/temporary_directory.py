# -*- coding: utf-8 -*-
# temporary_directory.py

"""
Class to create a temporary working directory, and clean up its contents afterwards
"""

import hashlib
import os
import time


class TemporaryDirectory:
    """
    Class to create a temporary working directory, and clean up its contents afterwards
    """

    def __init__(self):
        # Create a random hex id to use in the filename of the temporary directory
        key_string = str(time.time())
        uid = hashlib.md5(key_string.encode()).hexdigest()

        # Create temporary working directory
        identifier = uid[:32]
        id_string = "eas_{:d}_{}".format(os.getpid(), identifier)
        tmp_dir = os.path.join("/tmp", id_string)
        os.makedirs(name=tmp_dir, mode=0o700, exist_ok=True)

        self.tmp_dir = tmp_dir

    def __enter__(self):
        """
        Called at the start of a with block
        """
        return self

    def __del__(self):
        """
        Destructor
        """
        self.clean_up()

    def clean_up(self):
        """
        Clean up temporary directory
        """
        if self.tmp_dir is not None:
            os.rmdir(self.tmp_dir)
            self.tmp_dir = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called at the end of a with block
        """
        self.clean_up()
