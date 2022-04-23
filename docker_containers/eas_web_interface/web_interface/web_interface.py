#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# web_interface.py

from os import path as os_path
from flask import Flask, render_template, url_for
import argparse
import datetime
import time

from typing import Dict, List, Optional

from plato_wp36 import settings, task_database

# Instantiate flask http server
app = Flask(__name__)


def fetch_job_tree(job_name: Optional[str] = None, status: str = 'any'):
    """
    Fetch the hierarchy of jobs in the database.

    :return:
        List[Dict]
    """

    output: List[Dict] = []

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
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND x.startTime IS NULL) AS runs_queued,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND x.startTime IS NOT NULL AND
                    (x.errorFail OR (x.endTime IS NULL AND x.latestHeartbeat < {min_heartbeat:f}))) AS runs_stalled,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND x.startTime IS NOT NULL AND
                    x.endTime IS NULL AND NOT x.errorFail AND x.latestHeartbeat > {min_heartbeat:f}) AS runs_running,
   (SELECT COUNT(*) FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND x.endTime IS NOT NULL AND
                    NOT x.errorFail) AS runs_done
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
                            'id': parent['task']['taskId'],
                            'w': parent['task']['runs_queued'],
                            'r': parent['task']['runs_running'],
                            's': parent['task']['runs_stalled'],
                            'd': parent['task']['runs_done']
                        })

            # Search for child tasks
            search_children(parent_id=item['taskId'])

            # Pop this task from the hierarchy
            parents.pop()

    # Fetch job tree
    search_children()

    # Commit database
    task_db.commit()
    task_db.close_db()

    # Return results
    return output


# Index of all the tasks in the database
@app.route("/")
def task_index():
    # Fetch a list of all the tasks in the database
    task_list = fetch_job_tree()

    # Render list of SpectrumLibraries into HTML
    return render_template('index.html', task_table=task_list)


if __name__ == "__main__":
    # Read input parameters
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--public',
                        required=False,
                        action='store_true',
                        dest="public",
                        help="Make this python/flask instance publicly visible on the network.")
    parser.add_argument('--private',
                        required=False,
                        action='store_false',
                        dest="public",
                        help="Make this python/flask instance only visible on localhost (default).")
    parser.set_defaults(public=True)
    args = parser.parse_args()

    # Start web interface
    app.run(host="0.0.0.0" if args.public else "127.0.0.1")
