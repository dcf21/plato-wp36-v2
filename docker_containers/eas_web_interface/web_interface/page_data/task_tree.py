# -*- coding: utf-8 -*-
# task_tree.py

import time

from typing import Dict, List, Optional

from plato_wp36 import settings, task_database


def fetch_job_tree(job_name: Optional[str] = None, status: str = 'any'):
    """
    Fetch the hierarchy of jobs in the database.

    :return:
        List[Dict]
    """

    output: List[Dict] = []

    # Fetch EAS pipeline settings
    s = settings.Settings()

    def search_children(parent_id: int = None):
        # Build an SQL query for all tasks with the selected parent
        if parent_id is not None:
            constraint = "parentTask = {:d}".format(parent_id)
        else:
            constraint = "parentTask IS NULL"

        # The latest recorded heartbeat time at which a process is judged to be still running
        threshold_heartbeat_time = time.time() - s.installation_info['max_heartbeat_age']

        # Search for all tasks with a given parent
        task_db.db_handle.parameterised_query("""
SELECT t.taskId, t.jobName, ett.taskName,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND x.isQueued) AS runs_queued,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND
                    (x.errorFail OR (x.isRunning AND x.latestHeartbeat < {min_heartbeat:f}))) AS runs_stalled,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND
                    x.isRunning AND NOT x.errorFail AND x.latestHeartbeat > {min_heartbeat:f}) AS runs_running,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND
                    x.isFinished AND NOT x.errorFail) AS runs_done
FROM eas_task t
INNER JOIN eas_task_types ett on t.taskTypeId = ett.taskTypeId
WHERE {constraint} ORDER BY taskId;
""".format(constraint=constraint, min_heartbeat=threshold_heartbeat_time))

        task_list = task_db.db_handle.fetchall()

        # Display each task in turn, complete with subtasks
        for item in task_list:
            # Work out whether this task meets the user's chosen search criteria
            display_now = True
            if job_name is not None:
                if item['jobName'] != job_name:
                    display_now = False
            if (status == 'waiting') and ((item['runs_queued'] > 0) or (item['runs_running'] > 0) or
                                          (item['runs_stalled'] > 0) or (item['runs_done'] > 0)):
                display_now = False
            if (status == 'queued') and (item['runs_queued'] == 0):
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

                        html_class = 'waiting'
                        if parent['task']['runs_done'] > 0:
                            html_class = 'done'
                        elif parent['task']['runs_running'] > 0:
                            html_class = 'running'
                        elif parent['task']['runs_stalled'] > 0:
                            html_class = 'stalled'
                        elif parent['task']['runs_queued'] > 0:
                            html_class = 'queued'

                        output.append({
                            'indent': " &rarr; " * level,
                            'job_name': parent['job_name'],
                            'task_name': parent['task']['taskName'],
                            'class': html_class,
                            'task_id': parent['task']['taskId'],
                            'w': parent['task']['runs_queued'],
                            'r': parent['task']['runs_running'],
                            's': parent['task']['runs_stalled'],
                            'd': parent['task']['runs_done']
                        })

            # Search for child tasks
            search_children(parent_id=item['taskId'])

            # Pop this task from the hierarchy
            parents.pop()

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Stack of parent tasks
        parents = []

        # Fetch job tree
        search_children()

    # Return results
    return output
