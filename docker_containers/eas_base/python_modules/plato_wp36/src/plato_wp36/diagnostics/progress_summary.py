# -*- coding: utf-8 -*-
# progress_summary.py

import time

from typing import Optional

from plato_wp36 import settings, task_database


def fetch_progress_summary(job_name: Optional[str] = None):
    """
    Fetch task progress summary from the database.

    :param job_name:
            Filter the task tree in the database by job name.
    :return:
        Dict
    """

    # Fetch EAS pipeline settings
    s = settings.Settings()

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Build an SQL query for all matching log messages
        constraints = ["1"]
        parameters = []
        if job_name is not None:
            constraints.append("t.JobName = %s")
            parameters.append(job_name)

        # The latest recorded heartbeat time at which a process is judged to be still running
        threshold_heartbeat_time = time.time() - s.installation_info['max_heartbeat_age']

        # Search for all matching tasks
        task_db.db_handle.parameterised_query("""
SELECT tt.taskTypeName,
   s.isQueued IS NULL AS run_waiting,
   s.isQueued AS run_queued,
   s.errorFail OR (s.isRunning AND s.latestHeartbeat < {min_heartbeat:f}) AS run_stalled,
   s.isRunning AND NOT s.errorFail AND s.latestHeartbeat > {min_heartbeat:f} AS run_running,
   s.isFinished AND NOT s.errorFail AS run_done
FROM eas_task t
LEFT OUTER JOIN eas_scheduling_attempt s ON t.taskId = s.taskId
INNER JOIN eas_task_types tt ON tt.taskTypeId = t.taskTypeId
WHERE {constraint};
""".format(constraint=" AND ".join(constraints), min_heartbeat=threshold_heartbeat_time), tuple(parameters))

        task_list = task_db.db_handle.fetchall()

        # Compile results into a table
        output_table = {}
        for item in task_list:
            if item['taskTypeName'] not in output_table:
                output_table[item['taskTypeName']] = [0] * 5
            if item['run_waiting']:
                output_table[item['taskTypeName']][0] += item['run_waiting']
            else:
                if item['run_queued']:
                    output_table[item['taskTypeName']][1] += item['run_queued']
                if item['run_stalled']:
                    output_table[item['taskTypeName']][2] += item['run_stalled']
                if item['run_running']:
                    output_table[item['taskTypeName']][3] += item['run_running']
                if item['run_done']:
                    output_table[item['taskTypeName']][4] += item['run_done']

        # Format table
        output = {
            'column_headings': ('Task', 'Waiting', 'Queued', 'Stalled', 'Running', 'Done'),
            'rows': []
        }

        for task in sorted(output_table.keys()):
            item = output_table[task]
            norm = sum(item) + 1e-8
            output['rows'].append(
                [task] + ["{:d} ({:.0f}%)".format(col, col / norm * 100) for col in item]
            )

    # Return results
    return output
