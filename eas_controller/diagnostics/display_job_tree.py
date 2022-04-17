#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# display_job_tree.py

"""
Display the hierarchy of jobs in the database
"""

import argparse
import logging
import os
import time

from typing import Optional

from plato_wp36 import settings, task_database


def display_job_tree(job_name: Optional[str] = None, status: str = 'any'):
    """
    Display the hierarchy of jobs in the database

    :return:
        None
    """

    # Fetch testbench settings
    s = settings.Settings()

    # Open connection to the database
    task_db = task_database.TaskDatabaseConnection()

    # Stack of parent tasks
    parents = []

    def search_children(parent_id: int = None):
        # Build an SQL query for all tasks with the selected parent
        if parent_id is not None:
            constraint = "parentTask = {:d}".format(parent_id)
        else:
            constraint = "parentTask IS NULL"

        # The latest recorded heartbeat time at which a process is judged to be still running
        threshold_heartbeat_time = time.time() - s.installation_info['max_heartbeat_age']

        # Search for all tasks with a given parent
        task_db.conn.execute("""
SELECT t.taskId, t.jobName, ett.taskName,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND x.startTime IS NULL) AS runs_waiting,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND x.startTime IS NOT NULL AND
                    NOT x.allProductsPassedQc AND x.latestHeartbeat < {min_heartbeat:f}) AS runs_stalled,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND x.startTime IS NOT NULL AND
                    NOT x.allProductsPassedQc AND x.latestHeartbeat > {min_heartbeat:f}) AS runs_running,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND x.allProductsPassedQc) AS runs_done
FROM eas_task t
INNER JOIN eas_task_types ett on t.taskTypeId = ett.taskTypeId
WHERE {constraint} ORDER BY taskId;
""".format(constraint=constraint, min_heartbeat=threshold_heartbeat_time))

        task_list = task_db.conn.fetchall()

        # Display each task in turn, complete with subtasks
        for item in task_list:
            # Work out whether this task meets the user's chosen search criteria
            display_now = True
            if job_name is not None:
                if item['jobName'] != job_name:
                    display_now = False
                if (status == 'waiting') and (item['runs_waiting'] == 0):
                    display_now = False
                if (status == 'running') and (item['runs_running'] == 0):
                    display_now = False
                if (status == 'stalled') and (item['runs_stalled'] == 0):
                    display_now = False
                if (status == 'done') and (item['runs_done'] == 0):
                    display_now = False

            # Add this task to the hierarchy if parents
            parents.append({
                'job_name': item['jobName'] if item['jobName'] is not None else "<untitled>",
                'task': item,
                'shown': False
            })

            # If we are displaying this item, do so now, possibly with any parent we've not shown
            if display_now:
                for level, parent in enumerate(parents):
                    if not parent['shown']:
                        parent['shown'] = True
                        print('{indent}{job_name}/{task_name} ({id} - {w}/{r}/{s}/{d})'.format(
                            indent="  " * level,
                            job_name=parent['job_name'],
                            task_name=parent['task']['taskName'],
                            id=parent['task']['taskId'],
                            w=parent['task']['runs_waiting'],
                            r=parent['task']['runs_running'],
                            s=parent['task']['runs_stalled'],
                            d=parent['task']['runs_done']
                        ))

            # Search for child tasks
            search_children(parent_id=item['taskId'])

            # Pop this task from the hierarchy
            parents.pop()

    # Display job tree
    search_children()

    # Commit database
    task_db.commit()
    task_db.close_db()


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--job-name', default=None, type=str, dest='job_name',
                        help='Display jobs with a given name')
    parser.add_argument('--status', default='any', type=str, dest='status',
                        choices=['any', 'waiting', 'running', 'stalled', 'done'],
                        help='Display only jobs with a particular status')
    args = parser.parse_args()

    # Fetch testbench settings
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
