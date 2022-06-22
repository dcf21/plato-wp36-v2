# -*- coding: utf-8 -*-
# render_task_tree.py

import time

from typing import Optional

from plato_wp36 import settings, task_database


def fetch_running_job_tree(job_name: Optional[str] = None,
                           include_recently_finished: bool = False,
                           max_depth: Optional[int] = 20):
    """
    Fetch the hierarchy of jobs in the database which are marked as running.

    :param job_name:
        Filter the task tree in the database by job name.
    :param include_recently_finished:
        Boolean flag indicating whether we should include tasks which have finished within past 5 seconds.
    :param max_depth:
        Maximum depth of the task tree to descend to.
    :return:
        List of lines of output
    """

    # Fetch EAS pipeline settings
    s = settings.Settings()

    # The latest recorded heartbeat time at which a process is judged to be still running
    threshold_heartbeat_time = time.time() - s.installation_info['max_heartbeat_age']

    # Create SQL search criterion
    args = []
    criterion = "(x.isRunning AND NOT x.errorFail AND x.latestHeartbeat > {min_heartbeat:f})".format(
        min_heartbeat=threshold_heartbeat_time)
    if include_recently_finished:
        criterion += " OR x.endTime > {epoch:f}".format(epoch=time.time() - 5)

    if job_name is not None:
        criterion = "({}) AND t.jobName=%s".format(criterion)
        args.append(job_name)

    # Search for currently running tasks
    with task_database.TaskDatabaseConnection() as task_db:
        task_db.db_handle.parameterised_query("""
SELECT DISTINCT x.taskId
FROM eas_scheduling_attempt x
INNER JOIN eas_task t on t.taskId = x.taskId
WHERE {criterion}
ORDER BY x.taskId;
""".format(criterion=criterion), tuple(args))

        running_task_list = task_db.db_handle.fetchall()

        # Start building list of lines of output
        tree_structures = []
        search_tree_by_task_id = {}

        # Build tree for each running task
        for item in running_task_list:
            node = item['taskId']
            tree = None
            current_depth = 0

            while node is not None:
                # If this parent is already a parent of another running task, add this branch to the tree
                if node in search_tree_by_task_id:
                    if tree is not None:
                        search_tree_by_task_id[node]['children'].append(tree)
                        tree = None
                    break

                # Don't exceed maximum depth
                if max_depth is not None and current_depth >= max_depth:
                    break

                # Search for node
                task_db.db_handle.parameterised_query("""
SELECT t.taskId, t.jobName, ett.taskTypeName, t.parentTask,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND x.isQueued) AS runs_queued,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND
                    (x.errorFail OR (x.isRunning AND x.latestHeartbeat < {min_heartbeat:f}))) AS runs_stalled,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND
                    x.isRunning AND NOT x.errorFail AND x.latestHeartbeat > {min_heartbeat:f}) AS runs_running,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND
                    x.isFinished AND NOT x.errorFail) AS runs_done
FROM eas_task t
INNER JOIN eas_task_types ett on t.taskTypeId = ett.taskTypeId
WHERE t.taskId=%s;
""".format(min_heartbeat=threshold_heartbeat_time), (node,))
                item = task_db.db_handle.fetchall()[0]

                new_tree = {
                    'level': None,
                    'job_name': item['jobName'] if item['jobName'] is not None else "<untitled>",
                    'task_type_name': item['taskTypeName'],
                    'task_id': item['taskId'],
                    'w': item['runs_queued'],
                    'r': item['runs_running'],
                    's': item['runs_stalled'],
                    'd': item['runs_done'],
                    'tree_truncated': False,
                    'children': [tree]
                }
                tree = new_tree
                search_tree_by_task_id[item['taskId']] = new_tree
                node = item['parentTask']

            # Add this tree
            if tree is not None:
                tree_structures.append(tree)

    # Convert tree into lines of output
    output_lines = []

    def navigate_tree(node, level=0):
        node['level'] = level
        output_lines.append(node)
        for item in node['children']:
            if item is not None:
                navigate_tree(node=item, level=level + 1)

    for node in tree_structures:
        navigate_tree(node=node)

    # Return lines of output
    return output_lines


def fetch_job_tree(job_name: Optional[str] = None,
                   parent_id: Optional[int] = None,
                   max_depth: Optional[int] = 5):
    """
    Fetch the hierarchy of jobs in the database.

    :param job_name:
        Filter the task tree in the database by job name.
    :param parent_id:
        Only show tasks descended from a particular parent.
    :param max_depth:
        Maximum depth of the task tree to descend to.
    :return:
        List of lines of output
    """

    # Start building list of lines of output
    output = []

    # Fetch EAS pipeline settings
    s = settings.Settings()

    def search_children(parent_id: int = None, depth: int = 0):
        """
        Search for child tasks of a parent.

        :param parent_id:
            Search for tasks with a given parent.
        :param depth:
            Iteratively keep track of the depth within the hierarchy.
        :return:
            Boolean indicating whether the task tree has been truncated
        """
        # Build an SQL query for all tasks with the selected parent
        if parent_id is not None:
            constraint = "parentTask = %s"
            arguments = (parent_id,)
        else:
            if job_name is None:
                constraint = "parentTask IS NULL"
                arguments = ()
            else:
                constraint = """
jobName = %s AND NOT EXISTS (SELECT 1 FROM eas_task p WHERE p.jobName=%s AND p.taskId=t.parentTask)
"""
                arguments = (job_name, job_name)

        # The latest recorded heartbeat time at which a process is judged to be still running
        threshold_heartbeat_time = time.time() - s.installation_info['max_heartbeat_age']

        # Do not exceed maximum requested depth
        if max_depth is not None and depth >= max_depth:
            # Check if tree is being truncated
            task_db.db_handle.parameterised_query("""
SELECT COUNT(t.taskId) AS count
FROM eas_task t
WHERE {constraint} ORDER BY taskId;
""".format(constraint=constraint), arguments)

            task_count = task_db.db_handle.fetchall()[0]['count']
            return task_count > 0

        # Search for all tasks with a given parent
        task_db.db_handle.parameterised_query("""
SELECT t.taskId, t.jobName, ett.taskTypeName,
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
""".format(constraint=constraint, min_heartbeat=threshold_heartbeat_time), arguments)

        task_list = task_db.db_handle.fetchall()

        # Display each task in turn, complete with subtasks
        for item in task_list:
            # Work out whether this task meets the user's chosen search criteria
            display_now = True
            if job_name is not None:
                if item['jobName'] != job_name:
                    display_now = False

            # Item descriptor
            item_info = {}
            if display_now:
                item_info = {
                    'level': depth,
                    'job_name': item['jobName'] if item['jobName'] is not None else "<untitled>",
                    'task_type_name': item['taskTypeName'],
                    'task_id': item['taskId'],
                    'w': item['runs_queued'],
                    'r': item['runs_running'],
                    's': item['runs_stalled'],
                    'd': item['runs_done'],
                    'tree_truncated': False
                }
                output.append(item_info)

            # Search for child tasks
            truncated = search_children(parent_id=item['taskId'], depth=depth + 1)
            if truncated:
                item_info['tree_truncated'] = True

        # Task tree not truncated at this level
        return False

    # Fetch job tree
    with task_database.TaskDatabaseConnection() as task_db:
        search_children(parent_id=parent_id)

    # Return lines of output
    return output
