# -*- coding: utf-8 -*-
# activity_history.py

from plato_wp36 import task_database


def fetch_timeline():
    """
    Fetch log messages from the database.

    :return:
        dict
    """

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Search for all task-execution entries
        task_db.db_handle.parameterised_query("""
SELECT t.taskId, s.startTime, s.endTime, h.hostId, h.hostname, tt.taskTypeName
FROM eas_scheduling_attempt s
INNER JOIN eas_task t on t.taskId = s.taskId
INNER JOIN eas_task_types tt on tt.taskTypeId = t.taskTypeId
LEFT OUTER JOIN eas_worker_host h on h.hostId = s.hostId
ORDER BY s.startTime;
""")

        task_list = task_db.db_handle.fetchall()

        # Convert tasks into dictionaries
        output = []
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
            output.append({
                'id': item['taskId'],
                'group': item['hostId'],
                'content': text,
                'title': text,
                'start': item['startTime'] * 1000,
                'end': item['endTime'] * 1000
            })

    # Return results
    return groups, output
