#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# reschedule_all_unfinished_jobs.py

"""
(Re)schedule all unfinished tasks to be (re)-run.
"""

import argparse
import logging
import os

from plato_wp36 import settings, task_queues


def schedule_jobs():
    """
    (Re)schedule all unfinished tasks to be (re)-run.

    :return:
        None
    """

    with task_queues.TaskScheduler() as scheduler:
        scheduler.reschedule_all_unfinished_jobs()


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
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

    # Reschedule tasks
    schedule_jobs()
