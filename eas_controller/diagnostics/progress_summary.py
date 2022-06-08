#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# progress_summary.py

"""
Produce a table summarising the fraction of completed tasks in the task database
"""

import argparse
import logging
import os
import sys

from typing import Optional

from plato_wp36 import settings
from plato_wp36.diagnostics import progress_summary


def column_width(i: int):
    # Make first column extra-wide
    if i == 0:
        return 32
    return 15


def progress_table(job_name: Optional[str] = None):
    """
    Produce a table summarising the fraction of completed tasks in the task database.

    :param job_name:
        Filter results by job name.
    :type job_name:
        str
    """
    output = sys.stdout

    # Fetch table data
    table = progress_summary.fetch_progress_summary(job_name=job_name)

    # Display table headings
    for col_num, item in enumerate(table['column_headings']):
        col_width = column_width(col_num)
        output.write("{txt:>{width}s} ".format(txt=str(item), width=col_width))
    output.write("\n")

    # Display each row in turn
    for row in table['rows']:
        for col_num, item in enumerate(row):
            col_width = column_width(col_num)
            output.write("{txt:>{width}s} ".format(txt=str(item), width=col_width))
        output.write("\n")


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-name', default=None, type=str, dest='job_name', help='Filter results by job name')
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

    # Dump results
    progress_table(job_name=args.job_name)
