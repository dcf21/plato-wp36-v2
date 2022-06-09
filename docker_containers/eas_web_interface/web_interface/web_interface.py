#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# web_interface.py

import argparse
import magic
import os.path

from flask import Flask, Response, redirect, request, render_template, url_for
from urllib.parse import urlencode

from plato_wp36 import task_database
from plato_wp36.diagnostics import pass_fail_table, progress_summary, timings_table

from page_data import activity_history, file_explorer, log_messages, select_options, \
    task_status, task_tree

# Instantiate flask http server
app = Flask(__name__)


def read_get_arguments(search: dict):
    """
    Read the GET arguments received by flask into a dictionary, overriding default values.

    :param search:
        Default parameter values for every GET argument we are to look for.
    """
    for parameter in search:
        val = request.values.get(parameter)
        if val is None:
            continue
        elif val == '-- Any --':
            search[parameter] = None
        elif not (parameter.startswith('max_') or parameter in ('filter', 'include_recent', 'page', 'task_id')):
            try:
                search[parameter] = str(val)
            except (TypeError, ValueError):
                pass
        else:
            try:
                search[parameter] = int(val)
            except (TypeError, ValueError):
                pass


def write_get_arguments(search: dict):
    """
    Write a safe URL string containing all the GET arguments listed in the dictionary <search>
    """
    return urlencode(search)


def write_pager_list(result_list, get_data, self_url):
    """
    Write a list of the URLs used to display paginated results

    :param result_list:
        Data structure returned from our database search.
    :param get_data:
        The GET arguments which need to be preserved in the URL for each page
    :param self_url:
        The base URL for this webpage.
    """
    pager_list = []
    for page_num in range(result_list['show_page_min'], result_list['show_page_max'] + 1):
        pager_list.append({
            'num': page_num,
            'url': "{}?{}".format(self_url, write_get_arguments({**get_data, 'page': page_num}))
        })
    return pager_list


# Index of all the tasks in the database
@app.route("/", methods=('GET', 'POST'))
def task_index():
    # Fetch page search parameters
    search = {
        'job_name': None,
        'task_id': None,
        'max_depth': 5
    }
    read_get_arguments(search)

    # Fetch a list of all the tasks in the database
    self_url = url_for("task_index")
    task_list = task_tree.fetch_job_tree(**search, running_only=False, self_url=self_url)

    # Render list of tasks into HTML
    return render_template('index.html', task_table=task_list, self_url=self_url,
                           show_include_recent=False, show_max_depth=True,
                           max_depth_options=['-- Any --'] + list(range(7)),
                           job_name_options=['-- Any --'] + select_options.job_name_options(),
                           job_name=search['job_name'], max_depth=search['max_depth'],
                           show_back_arrow=bool(search['task_id'])
                           )


# Index of all the running tasks in the database
@app.route("/running", methods=('GET', 'POST'))
def task_running_index():
    # Fetch page search parameters
    search = {
        'job_name': None,
        'include_recent': 0,
        'max_depth': None
    }
    read_get_arguments(search)

    # Fetch a list of all the tasks in the database
    self_url = url_for("task_running_index")
    task_list = task_tree.fetch_job_tree(**search, running_only=True, self_url=self_url)

    # Render list of tasks into HTML
    return render_template('index.html', task_table=task_list, self_url=self_url,
                           show_include_recent=True, show_max_depth=False,
                           job_name_options=['-- Any --'] + select_options.job_name_options(),
                           job_name=search['job_name'], include_recent=search['include_recent'],
                           show_back_arrow=False
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
    # Check that task_id is integer
    try:
        task_id = int(task_id)
    except ValueError:
        return redirect(url_for('task_index'))

    # Fetch a list of information about all the attempts to run this task
    task_info = task_status.task_status(task_id=int(task_id))
    if task_info is None:
        return redirect(url_for('task_index'))

    # Render task information into HTML
    return render_template('task_info.html', task_id=int(task_id), task_info=task_info)


# Index of all the file directories in the database
@app.route("/directories")
def directory_index():
    # Fetch page search parameters
    search = {
        'page': 1
    }
    read_get_arguments(search)

    # Fetch a list of all the directories in the database
    directory_table = file_explorer.fetch_directory_list(page=search['page'])

    # Write pager list
    self_url = url_for("directory_index")
    pager_list = write_pager_list(result_list=directory_table, get_data=search, self_url=self_url)

    # Render list of directories into HTML
    return render_template('directories.html', item_table=directory_table, pager_list=pager_list)


# Index of all the file directories in the database
@app.route("/files/<directory>", methods=("GET", "POST"))
def file_index(directory):
    # Fetch page search parameters
    search = {
        'page': 1
    }
    read_get_arguments(search)

    # Fetch a list of all the files in the directory
    file_table = file_explorer.fetch_file_list(directory=directory, page=search['page'])

    # Write pager list
    self_url = url_for("file_index", directory=directory)
    pager_list = write_pager_list(result_list=file_table, get_data=search, self_url=self_url)

    # Render list of files into HTML
    return render_template('files.html', item_table=file_table, pager_list=pager_list)


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


# Summary of the fraction of tasks which have completed
@app.route("/progress")
def progress_index():
    # Fetch page search parameters
    search = {
        'job_name': None
    }
    read_get_arguments(search)

    # Fetch progress summary table
    progress_table = progress_summary.fetch_progress_summary(**search)

    # Render list of timing data into HTML
    self_url = url_for("progress_index")
    return render_template('progress.html', progress_summary=progress_table, self_url=self_url,
                           job_name=search['job_name'],
                           job_name_options=['-- Any --'] + select_options.job_name_options()
                           )


# Index of all log messages in the database
@app.route("/logs")
def log_index():
    # Fetch page search parameters
    search = {
        'min_severity': 'warning',
        'page': 1
    }
    read_get_arguments(search)

    # Fetch a list of all the log messages in the database
    log_list = log_messages.fetch_log_messages(**search)

    # Write pager list
    self_url = url_for("log_index")
    pager_list = write_pager_list(result_list=log_list, get_data=search, self_url=self_url)

    # Render list of log messages into HTML
    return render_template('logs.html', log_table=log_list, self_url=self_url, min_severity=search['min_severity'],
                           pager_list=pager_list,
                           severity_options=('-- Any --', 'warning', 'error'))


# Show a timeline of tasks running on the cluster
@app.route("/timeline")
def activity_timeline():
    # Fetch page search parameters
    search = {
        'filter': 0
    }
    read_get_arguments(search)
    item_table = activity_history.fetch_timeline(filter_type=int(search['filter']))

    # Render page
    self_url = url_for("activity_timeline")
    return render_template('timeline.html', self_url=self_url, item_table=item_table, filter=int(search['filter']),
                           filter_options=(
                               (0, "Latest 200 tasks"),
                               (1, "Tasks running for over 60 seconds"),
                               (2, "Tasks running for over 2 seconds"),
                               (99, "All tasks")
                           ))


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
