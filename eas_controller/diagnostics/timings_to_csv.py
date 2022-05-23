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

from plato_wp36 import settings, task_database


def render_run_time(input):
    if input is None:
        return "-"
    else:
        return "{:.2f}".format(input)


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
    output = sys.stdout

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Fetch list of jobs
        task_db.db_handle.parameterised_query("SELECT DISTINCT jobName FROM eas_task ORDER BY jobName;")
        job_list = [item['jobName'] for item in task_db.db_handle.fetchall()]

        if job_name is not None:
            job_list = [item for item in job_list if item == job_name]

        # Fetch list of task types (but to save space, don't show internal execution_ task types)
        task_db.db_handle.parameterised_query("SELECT taskTypeName FROM eas_task_types ORDER BY taskTypeName;")
        task_list = [item['taskTypeName']
                     for item in task_db.db_handle.fetchall()
                     if not item['taskTypeName'].startswith('execution_')]

        if task_type is not None:
            task_list = [item for item in task_list if item == task_type]

        # Loop over job names
        for job_name in job_list:

            # Loop over task types
            for task_type in task_list:

                # Fetch list of all the tasks we need to display
                task_db.db_handle.parameterised_query("""
SELECT runTimeWallClock, runTimeCpu, runTimeCpuIncChildren, et.taskId
FROM eas_scheduling_attempt s
INNER JOIN eas_task et on et.taskId = s.taskId
INNER JOIN eas_task_types ett on ett.taskTypeId = et.taskTypeId
WHERE et.jobName=%s AND ett.taskTypeName=%s
ORDER BY schedulingAttemptId;
""", (job_name, task_type)
                                                      )
                results = list(task_db.db_handle.fetchall())

                # Abort if no database entries matched this search
                if len(results) < 1:
                    continue

                # Fetch numerical input parameters to each task
                metadata_per_item = []
                all_parameter_names = []
                for result in results:
                    metadata = task_db.metadata_fetch_all(task_id=result['taskId'])
                    metadata_per_item.append(metadata)

                    for keyword in tuple(metadata.keys()):
                        # Purge very long values
                        if len(str(metadata[keyword].value)) > 25:
                            del metadata[keyword]
                            continue
                        # Keep track of all metadata field names
                        if keyword not in all_parameter_names:
                            all_parameter_names.append(keyword)

                # Sort parameter names alphabetically
                all_parameter_names.sort()

                # Display heading for this job
                output.write("\n\n{}  --  {}\n\n".format(job_name, task_type))

                # List of run-time metrics
                run_time_metrics = ["runTimeWallClock", "runTimeCpu", "runTimeCpuIncChildren"]

                # Display column headings
                output.write("# ")
                for item in all_parameter_names + run_time_metrics:
                    output.write("{:12.12}  ".format(item))
                output.write("\n")

                # Display results
                for metadata, result in zip(metadata_per_item, results):
                    # Display parameter values
                    for item in all_parameter_names:
                        if item in metadata:
                            value_string = metadata[item].value
                        else:
                            value_string = "--"
                        try:
                            value_float = float(value_string)
                            output.write("{:12.8f}  ".format(value_float))
                        except ValueError:
                            output.write("{:12.12s}  ".format(str(value_string)))

                    # Loop over timing metrics
                    for metric in run_time_metrics:
                        # Display results
                        output.write("{:12.12s} ".format(render_run_time(input=result[metric])))

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
