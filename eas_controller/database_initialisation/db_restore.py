#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# db_restore.py

"""
Import a task database from a gzipped database dump file.
"""

import argparse
import logging
import os

from plato_wp36 import connect_db, settings


def db_restore(input_filename: str):
    """
    Restore the task database from a gzipped dump file.

    :param input_filename:
        Filename of gzipped database dump
    """

    # Instantiate database connection class
    with connect_db.DatabaseConnector().interface(connect=True) as db:
        db.restore(input_filename=input_filename)


# Do it right away if we're run as a script
if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=str, dest='input',
                        help='Filename of the database dump to import')
    args = parser.parse_args()

    # Fetch EAS pipeline settings
    settings = settings.Settings()

    # Set up logging
    log_file_path = os.path.join(settings.settings['dataPath'], 'plato_wp36.log')
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        handlers=[
                            logging.FileHandler(log_file_path),
                            logging.StreamHandler()
                        ])
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # Initialise schema
    db_restore(input_filename=args.input)
