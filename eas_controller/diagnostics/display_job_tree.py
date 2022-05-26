#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# display_job_tree.py

"""
Display the hierarchy of jobs in the database
"""

import argparse
import logging
import os

from typing import Dict, Optional

from plato_wp36 import settings

from plato_wp36.diagnostics import render_task_tree


def display_job_tree(job_name: Optional[str] = None, status: str = 'any', max_depth: Optional[int] = None):
    """
    Display the hierarchy of jobs in the database.

    :param job_name:
        Filter the task tree in the database by job name.
    :param status:
        Filter the task tree by job status.
    :param max_depth:
        Maximum depth of the task tree to descend to.
    :return:
        None
    """

    def add_tree_item(item: Dict):
        item['indent'] = " | " * item['level']
        print('{indent}{job_name}/{task_type_name} ({task_id} - {w}/{r}/{s}/{d})'.format(**item))

    render_task_tree.fetch_job_tree(
        renderer=add_tree_item,
        job_name=job_name,
        status=status,
        max_depth=max_depth
    )


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-name', default=None, type=str, dest='job_name',
                        help='Display jobs with a given name')
    parser.add_argument('--status', default='any', type=str, dest='status',
                        choices=['any', 'waiting', 'queued', 'running', 'stalled', 'done'],
                        help='Display only jobs with a particular status')
    args = parser.parse_args()

    # Fetch EAS pipeline settings
    s = settings.Settings()

    # Set up logging
    log_file_path = os.path.join(s.settings['dataPath'], 'plato_wp36.log')
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        handlers=[
                            logging.FileHandler(log_file_path),
                            logging.StreamHandler()
                        ])
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # Display job tree
    display_job_tree(job_name=args.job_name, status=args.status)
