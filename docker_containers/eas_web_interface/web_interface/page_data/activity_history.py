# -*- coding: utf-8 -*-
# activity_history.py

import json
import time

from plato_wp36 import task_database


def fetch_timeline(filter_type: int):
    """
    Fetch log messages from the database.

    :return:
        dict
    """

    # Default filter: latest 200 tasks
    filter_str = "1"
    limit = 200

    if filter_type == 1:
        # All tasks running for over 60 sec
        filter_str = "s.runTimeWallClock > 60 OR s.isRunning"
        limit = 500
    elif filter_type == 2:
        # All tasks running for over 2 sec
        filter_str = "s.runTimeWallClock > 2 OR s.isRunning"
        limit = 500
    elif filter_type == 99:
        # Show all tasks
        filter_str = "1"
        limit = 800

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Count all matching task-executions
        task_db.db_handle.parameterised_query("""
SELECT COUNT(s.schedulingAttemptId) AS count
FROM eas_scheduling_attempt s
WHERE s.startTime IS NOT NULL AND {filter};
""".format(filter=filter_str))

        item_count = task_db.db_handle.fetchall()[0]['count']

        # Search for all task-execution entries
        task_db.db_handle.parameterised_query("""
SELECT t.taskId, s.startTime, s.endTime, h.hostId, h.hostname, tt.taskTypeName
FROM eas_scheduling_attempt s
INNER JOIN eas_task t on t.taskId = s.taskId
INNER JOIN eas_task_types tt on tt.taskTypeId = t.taskTypeId
LEFT OUTER JOIN eas_worker_host h on h.hostId = s.hostId
WHERE s.startTime IS NOT NULL AND {filter}
ORDER BY s.startTime DESC
LIMIT {limit:d};
""".format(filter=filter_str, limit=limit))

        task_list = task_db.db_handle.fetchall()

        # Convert tasks into dictionaries
        output_list = []
        groups = []
        groups_seen = []
        for item in task_list:
            # Create groupings of task running on each worker
            if item['hostId'] not in groups_seen:
                groups_seen.append(item['hostId'])
                groups.append({
                    'id': item['hostId'],
                    'content': item['hostname']
                })

            # Create entry for each individual task
            text = "#{:d} {}".format(item['taskId'], item['taskTypeName'])

            # If task is still running, then set its end time to now
            end_time = item['endTime']
            if end_time is None:
                end_time = time.time()

            # Create data point for this task
            output_list.append({
                'id': item['taskId'],
                'group': item['hostId'],
                'content': text,
                'title': text,
                'start': item['startTime'] * 1000,
                'end': end_time * 1000
            })

    # Return results
    return {
        'total_items': item_count,
        'groups': groups,
        'item_count': len(output_list),
        'item_list': json.dumps(output_list)
    }
