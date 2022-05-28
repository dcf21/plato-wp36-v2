#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# timings_to_csv.py

"""
Dump all the run times from the task database into a CSV file
"""

import argparse
import logging
import os
import sys

from typing import Optional

from plato_wp36 import settings
from plato_wp36.diagnostics import timings_table


def timings_to_csv(job_name: Optional[str] = None, task_type: Optional[str] = None):
    """
    List timings stored in the SQL database.

    :param job_name:
        Filter results by job name.
    :type job_name:
        str
    :param task_type:
        Filter results by type of task.
    :type task_type:
        str
    """

    table_info = timings_table.fetch_timings_table(job_name=job_name, task_type=task_type)

    output = sys.stdout

    # Display each data table in turn
    for table in table_info:
        # Display heading for this job
        output.write("\n\n{}\n\n".format(table['title']))

        # Display column headings
        output.write("# ")
        for item in table['column_headings']:
            output.write("{:12.12}  ".format(item))
        output.write("\n")

        # Display results
        for row in table['data_rows']:
            # Display parameter values
            for item in row['row_str']:
                output.write("{:12.12s}  ".format(str(item)))

            # New line
            output.write("\n")


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-name', default=None, type=str, dest='job_name', help='Filter results by job name')
    parser.add_argument('--task-type', default=None, type=str, dest='task_type', help='Filter results by task type')
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

    # Dump timings
    timings_to_csv(job_name=args.job_name, task_type=args.task_type)
