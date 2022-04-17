#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# submit.py

"""
Populate message queue with a group of tasks defined in a JSON file, which may include iterations.
"""

import logging
import os

import argparse
from plato_wp36 import settings, task_database, task_objects


def create_task(from_file: str):
    """
    Create a new task in the database representing an execution chain that we are to run.

    :param from_file:
        The filename of the file containing the JSON description of the execution chain
    :return:
        None
    """

    # Open a connection to the database
    task_db = task_database.TaskDatabaseConnection()
    task_db.task_register(
        task_type="execution_chain",
        metadata={
            "chain": task_objects.MetadataItem(keyword="chain", value=open(from_file).read())
        }
    )

    # Commit database
    task_db.commit()
    task_db.close_db()


# Do it right away if we're run as a script
if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tasks',
                        default="../../demo_jobs/202102_planet_detection_limit/earth_vs_size_psls.json",
                        type=str,
                        dest='tasks', help='The JSON file listing the execution chain we are to perform')

    args = parser.parse_args()

    # Fetch testbench settings
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
    logger.info("Running execution chain <{}>".format(args.tasks))

    # Create a new task in the database
    create_task(from_file=args.tasks)
