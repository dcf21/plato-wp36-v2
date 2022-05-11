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
        # Create a random hex id
        key_string = str(time.time())
        uid = hashlib.md5(key_string.encode()).hexdigest()

        # Create temporary working directory
        identifier = uid[:32]
        id_string = "eas_{:d}_{}".format(os.getpid(), identifier)
        tmp_dir = os.path.join("/tmp", id_string)
        os.makedirs(name=tmp_dir, mode=0o700, exist_ok=True)

        self.tmp_dir = tmp_dir

    def __enter__(self):
        pass

    def __del__(self):
        self.clean_up()

    def clean_up(self):
        # Clean up temporary directory
        if self.tmp_dir is not None:
            os.rmdir(self.tmp_dir)
            self.tmp_dir = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.clean_up()
