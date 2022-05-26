#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# web_interface.py


from flask import Flask, redirect, render_template, url_for
import argparse

from page_data import file_explorer, task_status, task_tree, log_messages

# Instantiate flask http server
app = Flask(__name__)


# Index of all the tasks in the database
@app.route("/")
def task_index():
    # Fetch a list of all the tasks in the database
    task_list = task_tree.fetch_job_tree()

    # Render list of tasks into HTML
    return render_template('index.html', task_table=task_list)


# Index of all the tasks in the database
@app.route("/task/<taskId>", methods=("GET", "POST"))
def task_info(taskId):
    # Fetch a list of information about all the attempts to run this task
    task_info = task_status.task_status(task_id=int(taskId))
    if task_info is None:
        return redirect(url_for('task_index'))

    # Render task information into HTML
    return render_template('task_info.html', task_id=int(taskId), task_info=task_info)


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


# Index of all log messages in the database
@app.route("/logs")
def log_index():
    # Fetch a list of all the log messages in the database
    log_list = log_messages.fetch_log_messages()

    # Render list of log messages into HTML
    return render_template('logs.html', log_table=log_list)


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
