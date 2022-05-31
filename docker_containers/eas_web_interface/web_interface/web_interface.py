#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# web_interface.py

import argparse
import json
import magic
import os.path

from flask import Flask, Response, redirect, request, render_template, url_for

from plato_wp36 import task_database
from plato_wp36.diagnostics import timings_table, pass_fail_table

from page_data import activity_history, file_explorer, log_messages, select_options, task_status, task_tree

# Instantiate flask http server
app = Flask(__name__)


def read_get_arguments(search):
    for parameter in search:
        val = request.values.get(parameter)
        if val == '-- Any --' or val is None:
            search[parameter] = None
        elif not parameter.startswith('max_'):
            try:
                search[parameter] = str(val)
            except (TypeError, ValueError):
                pass
        else:
            try:
                search[parameter] = int(val)
            except (TypeError, ValueError):
                pass


# Index of all the tasks in the database
@app.route("/", methods=('GET', 'POST'))
def task_index():
    # Fetch page search parameters
    search = {
        'job_name': None,
        'status': None,
        'max_depth': None
    }
    read_get_arguments(search)

    # Fetch a list of all the tasks in the database
    task_list = task_tree.fetch_job_tree(**search)

    # Render list of tasks into HTML
    self_url = url_for("task_index")
    return render_template('index.html', task_table=task_list, self_url=self_url,
                           status_options=('-- Any --', 'queued', 'waiting', 'done', 'running', 'stalled'),
                           max_depth_options=['-- Any --'] + list(range(5)),
                           job_name_options=['-- Any --'] + select_options.job_name_options(),
                           status=search['status'], job_name=search['job_name'], max_depth=search['max_depth']
                           )


# Index of all the tasks in the database
@app.route("/file/<product_version_id>/<filename>")
def file_fetch(product_version_id, filename):
    # Fetch path to file
    with task_database.TaskDatabaseConnection() as task_db:
        file_path = task_db.file_version_path_for_id(product_version_id=int(product_version_id))

    # Check file exists
    if not os.path.isfile(file_path):
        return redirect(url_for('task_index'))

    # Determine mime type for file
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)

    # Serve file
    content = open(file_path, "rb").read()
    return Response(content, mimetype=mime_type)


# Index of all the tasks in the database
@app.route("/task/<task_id>", methods=("GET", "POST"))
def task_info(task_id):
    # Fetch a list of information about all the attempts to run this task
    task_info = task_status.task_status(task_id=int(task_id))
    if task_info is None:
        return redirect(url_for('task_index'))

    # Render task information into HTML
    return render_template('task_info.html', task_id=int(task_id), task_info=task_info)


# Index of all the file directories in the database
@app.route("/directories")
def directory_index():
    # Fetch a list of all the directories in the database
    directory_list = file_explorer.fetch_directory_list()

    # Render list of directories into HTML
    return render_template('directories.html', item_list=directory_list)


# Index of all the file directories in the database
@app.route("/files/<directory>", methods=("GET", "POST"))
def file_index(directory):
    # Fetch a list of all the files in the directory
    file_list = file_explorer.fetch_file_list(directory=directory)

    # Render list of files into HTML
    return render_template('files.html', item_list=file_list)


# Index of all the task timing data in the database
@app.route("/timings")
def timing_index():
    # Fetch page search parameters
    search = {
        'job_name': None,
        'task_type': None
    }
    read_get_arguments(search)

    # Fetch a list of all timing data in the database
    timing_list = timings_table.fetch_timings_table(**search)

    # Render list of timing data into HTML
    self_url = url_for("timing_index")
    return render_template('timings.html', timing_info=timing_list, self_url=self_url,
                           job_name=search['job_name'], task_type=search['task_type'],
                           job_name_options=['-- Any --'] + select_options.job_name_options(),
                           task_type_options=['-- Any --'] + select_options.task_type_options()
                           )


# Index of all the task timing data in the database
@app.route("/pass_fail")
def pass_fail_index():
    # Fetch page search parameters
    search = {
        'job_name': None,
        'task_type': None
    }
    read_get_arguments(search)

    # Fetch a list of all pass/fail data in the database
    pass_fail_list = pass_fail_table.fetch_pass_fail_table(**search)

    # Render list of timing data into HTML
    self_url = url_for("pass_fail_index")
    return render_template('pass_fail.html', pass_fail_info=pass_fail_list, self_url=self_url,
                           job_name=search['job_name'], task_type=search['task_type'],
                           job_name_options=['-- Any --'] + select_options.job_name_options(),
                           task_type_options=['-- Any --'] + select_options.task_type_options()
                           )


# Index of all log messages in the database
@app.route("/logs")
def log_index():
    # Fetch page search parameters
    search = {
        'min_severity': None
    }
    read_get_arguments(search)

    # Fetch a list of all the log messages in the database
    log_list = log_messages.fetch_log_messages(**search)

    # Render list of log messages into HTML
    self_url = url_for("log_index")
    return render_template('logs.html', log_table=log_list, self_url=self_url, min_severity=search['min_severity'],
                           severity_options=('-- Any --', 'warning', 'error'))


# Show a timeline of tasks running on the cluster
@app.route("/timeline")
def activity_timeline():
    groups, timeline = activity_history.fetch_timeline()

    # Render page
    self_url = url_for("activity_timeline")
    return render_template('timeline.html', self_url=self_url, groups=groups,
                           activity_history=json.dumps(timeline))


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
