# -*- coding: utf-8 -*-
# log_messages.py

from datetime import datetime

from typing import Dict, List, Optional

from plato_wp36 import task_database


def fetch_log_messages(attempt_id: Optional[int] = None,
                       task_id: Optional[int] = None,
                       min_severity: Optional[int] = None):
    """
    Fetch log messages from the database.

    :param attempt_id:
        Fetch only log messages associated with one particular task execution.
    :param task_id:
        Fetch only log messages associated with one particular task.
    :param min_severity:
        Fetch only log messages with a minimum severity level.

    :return:
        List[Dict]
    """

    output: List[Dict] = []

    # Open connection to the database
    task_db = task_database.TaskDatabaseConnection()

    # Build an SQL query for all matching log messages
    constraints = ["1"]
    if attempt_id is not None:
        constraints.append("l.generatedByTaskExecution = {:d}".format(attempt_id))
    if task_id is not None:
        constraints.append("et.taskId = {:d}".format(task_id))
    if min_severity is not None:
        constraints.append("l.severity >= {:d}".format(min_severity))

    # Search for all tasks with a given parent
    task_db.conn.execute("""
SELECT l.timestamp, l.generatedByTaskExecution, l.severity, l.message
FROM eas_log_messages l
INNER JOIN eas_scheduling_attempt esa on l.generatedByTaskExecution = esa.schedulingAttemptId
INNER JOIN eas_task et on esa.taskId = et.taskId
WHERE {constraint}
ORDER BY generatedByTaskExecution, timestamp;
""".format(constraint=" AND ".join(constraints)))

    log_list = task_db.conn.fetchall()

    # Convert log events into dictionaries
    for item in log_list:
        message_class = 'info'
        if item['severity'] >= 30:
            message_class = 'warning'
        if item['severity'] >= 40:
            message_class = 'error'

        output.append({
            'attempt_id': item['generatedByTaskExecution'],
            'time': datetime.utcfromtimestamp(item['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
            'class': message_class,
            'message': item['message'].strip()
        })

    # Commit database
    task_db.commit()
    task_db.close_db()

    # Return results
    return output
