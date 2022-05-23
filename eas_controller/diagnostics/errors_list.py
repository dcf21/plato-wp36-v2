#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# errors_list.py

"""
Produce a list of all the error messages in the task database
"""

import logging
import os
import sys
from datetime import datetime

from typing import Optional

import argparse
from plato_wp36 import settings, task_database


def errors_list(job_name: Optional[str] = None, task_type: Optional[str] = None):
    """
    List error messages stored in the task database.

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
        # Fetch list of error messages
        task_db.db_handle.parameterised_query("""
SELECT l.timestamp, l.message, t.jobName, ty.taskTypeName AS taskType
FROM eas_log_messages l
LEFT OUTER JOIN eas_scheduling_attempt s ON s.schedulingAttemptId = l.generatedByTaskExecution
LEFT OUTER JOIN eas_task t ON s.taskId = t.taskId
LEFT OUTER JOIN eas_task_types ty ON ty.taskTypeId = t.taskTypeId
WHERE l.severity >= 40
ORDER BY l.timestamp;
""")
        results_list = task_db.db_handle.fetchall()

        # Loop over error messages
        for item in results_list:
            # Filter results
            if job_name is not None and job_name != item['jobName']:
                continue
            if task_type is not None and task_type != item['taskType']:
                continue

            # Display results
            time_string = datetime.utcfromtimestamp(item['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            output.write("{} |{:36s}|{:18s}|{}\n".format(
                time_string, item['jobName'], item['taskType'], item['message'].strip()
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

    # Dump results
    errors_list(job_name=args.job_name, task_type=args.task_type)
