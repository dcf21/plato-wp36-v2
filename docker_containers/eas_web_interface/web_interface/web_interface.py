#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# web_interface.py


from flask import Flask, render_template, url_for
import argparse

from page_data import task_tree, log_messages

# Instantiate flask http server
app = Flask(__name__)


# Index of all the tasks in the database
@app.route("/")
def task_index():
    # Fetch a list of all the tasks in the database
    task_list = task_tree.fetch_job_tree()

    # Render list of SpectrumLibraries into HTML
    return render_template('index.html', task_table=task_list)


# Index of all the tasks in the database
@app.route("/task/<taskId>", methods=("GET", "POST"))
def task_info(taskId):
    # Fetch a list of all the log messages in the database
    log_list = log_messages.fetch_log_messages(task_id=int(taskId))

    # Render list of SpectrumLibraries into HTML
    return render_template('task_info.html', log_table=log_list)


# Index of all log messages in the database
@app.route("/logs")
def log_index():
    # Fetch a list of all the log messages in the database
    log_list = log_messages.fetch_log_messages()

    # Render list of SpectrumLibraries into HTML
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
