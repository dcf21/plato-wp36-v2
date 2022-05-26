#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# db_save.py

"""
Create a gzipped database dump file.
"""

import argparse
import logging
import os
import time

from plato_wp36 import connect_db, settings


def db_dump(output_filename: str):
    """
    Create a database dump.

    :param output_filename:
        Filename for gzipped database dump
    """

    # Instantiate database connection class
    with connect_db.DatabaseConnector().interface(connect=True) as db:
        db.dump(output_filename=output_filename)


# Do it right away if we're run as a script
if __name__ == "__main__":
    output_filename = time.strftime("%Y%m%d_%H%M%S.sql.gz")

    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default=output_filename, type=str, dest='output',
                        help='Filename for database dump')
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
    db_dump(output_filename=args.output)
