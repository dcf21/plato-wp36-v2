#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# timings_list.py

"""
Produce the list of all the run times in the task database
"""

import argparse
import logging
import os
import sys
from datetime import datetime

from typing import Optional

from plato_wp36 import settings, task_database


def render_time(timestamp):
    """
    Render a unix time stamp as a human-readable string.

    :param timestamp:
        Unix timestamp (or None)
    """
    if timestamp is None:
        return "-"
    else:
        return datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')


def render_run_time(input):
    """
    Render the run-time of a task, in seconds.

    :param input:
        The run time (or None)
    """
    if input is None:
        return "-"
    else:
        return "{:.2f}".format(input)


def timings_list(job_name: Optional[str] = None, task_type: Optional[str] = None):
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
    output = sys.stdout

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Fetch list of timings
        task_db.db_handle.parameterised_query("""
SELECT startTime, runTimeWallClock, runTimeCpu, runTimeCpuIncChildren, et.taskId, et.jobName, ett.taskTypeName
FROM eas_scheduling_attempt s
INNER JOIN eas_task et on et.taskId = s.taskId
INNER JOIN eas_task_types ett on ett.taskTypeId = et.taskTypeId
ORDER BY schedulingAttemptId;
""")
        results = task_db.db_handle.fetchall()

        # Loop over task execution attempts
        for item in results:
            # Filter results
            if job_name is not None and job_name != item['jobName']:
                continue
            if task_type is not None and task_type != item['taskType']:
                continue

            # Display results
            time_string = render_time(timestamp=item['startTime'])
            output.write("{:20.20s} |{:36.36s}|{:18.18s}|{:12.12s}|{:12.12s}|{:12.12s}\n".format(
                time_string,
                str(item['jobName']), item['taskTypeName'],
                render_run_time(input=item['runTimeWallClock']),
                render_run_time(input=item['runTimeCpu']),
                render_run_time(input=item['runTimeCpuIncChildren'])
            ))


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
    timings_list(job_name=args.job_name, task_type=args.task_type)
