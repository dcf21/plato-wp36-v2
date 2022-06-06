# -*- coding: utf-8 -*-
# log_messages.py

from datetime import datetime
from math import ceil
from typing import Dict, List, Optional

from plato_wp36 import task_database


def fetch_log_messages(attempt_id: Optional[int] = None,
                       task_id: Optional[int] = None,
                       min_severity: Optional[int] = None,
                       page: int = 1,
                       page_size: int = 200):
    """
    Fetch log messages from the database.

    :param attempt_id:
        Fetch only log messages associated with one particular task execution.
    :param task_id:
        Fetch only log messages associated with one particular task.
    :param min_severity:
        Fetch only log messages with a minimum severity level.
    :param page:
        Page number of results.
    :param page_size:
        Size of each page of results.

    :return:
        List[Dict]
    """

    # Turn string severity levels into integers
    if min_severity == 'warning':
        min_severity = 30
    elif min_severity == 'error':
        min_severity = 40
    elif isinstance(min_severity, str):
        min_severity = 0

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Build an SQL query for all matching log messages
        constraints = ["1"]
        if attempt_id is not None:
            constraints.append("l.generatedByTaskExecution = {:d}".format(attempt_id))
        if task_id is not None:
            constraints.append("et.taskId = {:d}".format(task_id))
        if min_severity is not None:
            constraints.append("l.severity >= {:d}".format(min_severity))

        # Count number of matching log messages
        task_db.db_handle.parameterised_query("""
SELECT COUNT(*)
FROM eas_log_messages l
LEFT JOIN eas_scheduling_attempt esa on l.generatedByTaskExecution = esa.schedulingAttemptId
LEFT JOIN eas_task et on esa.taskId = et.taskId
WHERE {constraint}
ORDER BY generatedByTaskExecution, timestamp;
""".format(constraint=" AND ".join(constraints)))

        log_count = int(task_db.db_handle.fetchall()[0]['COUNT(*)'])

        # Work out paging request
        page = int(page)
        page_size = int(page_size)
        result_limit = int(page_size)
        result_offset = (page - 1) * page_size
        if result_offset > log_count:
            page = 1
            result_offset = 0
        page_max = max(1, int(ceil(log_count / page_size)))

        # Search for all matching log messages
        task_db.db_handle.parameterised_query("""
SELECT l.timestamp, l.generatedByTaskExecution, l.severity, l.message, et.taskId
FROM eas_log_messages l
LEFT JOIN eas_scheduling_attempt esa on l.generatedByTaskExecution = esa.schedulingAttemptId
LEFT JOIN eas_task et on esa.taskId = et.taskId
WHERE {constraint}
ORDER BY generatedByTaskExecution, timestamp
LIMIT {limit} OFFSET {offset};
""".format(constraint=" AND ".join(constraints), limit=result_limit, offset=result_offset))

        log_list = task_db.db_handle.fetchall()

        # Start building output
        output_list: List[Dict] = []

        result_min = int(result_offset + 1)
        result_max = int(result_offset + len(log_list))

        output = {
            'result_count': log_count,
            'result_count_str': "{:,}".format(log_count),
            'result_min': result_min,
            'result_max': result_max,
            'result_min_str': "{:,}".format(result_min),
            'result_max_str': "{:,}".format(result_max),
            'page_number': page,
            'page_max': page_max,
            'show_page_min': max(1, page - 8),
            'show_page_max': min(page_max, page + 7),
            'list': output_list
        }

        # Convert log events into dictionaries
        for item in log_list:
            message_class = 'info'
            if item['severity'] >= 30:
                message_class = 'warning'
            if item['severity'] >= 40:
                message_class = 'error'

            output_list.append({
                'attempt_id': item['generatedByTaskExecution'],
                'task_id': item['taskId'],
                'time': datetime.utcfromtimestamp(item['timestamp']).strftime('%Y-%m-%d %H:%M:%S'),
                'class': message_class,
                'message': item['message'].strip()
            })

    # Return results
    return output
