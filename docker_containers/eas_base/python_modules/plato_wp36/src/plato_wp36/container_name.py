# -*- coding: utf-8 -*-
# container_name.py

"""
Module for fetching the name of the Docker container that we are running within. We use this to determine
what tasks we are capable of running.
"""

import os

from typing import Optional

from .settings import Settings


def get_container_name(container_name_filename: Optional[str] = None):
    """
    Read the contents of a text file in the root of the Docker container, which tells us the name of the
    container we are running within.

    :param container_name_filename:
        The filename of the text file telling us which container is running
    :type container_name_filename:
        str
    :return:
        Name of container
    """

    # Fetch EAS settings
    settings = Settings().settings

    # Default path for name of container
    if container_name_filename is None:
        container_name_filename = os.path.join(settings['pythonPath'], '../../container_name.txt')

    with open(container_name_filename) as in_stream:
        container_name = in_stream.read().strip()

    return container_name
