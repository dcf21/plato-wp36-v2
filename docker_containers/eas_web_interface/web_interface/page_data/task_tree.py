# -*- coding: utf-8 -*-
# task_tree.py

from typing import Dict, List, Optional
from urllib.parse import urlencode

from plato_wp36.diagnostics import render_task_tree


def fetch_job_tree(self_url: str, task_id: Optional[int] = None,
                   job_name: Optional[str] = None, max_depth: Optional[int] = None, running_only: bool = False,
                   include_recent: bool = False):
    """
    Fetch the hierarchy of jobs in the database.

    :param self_url:
        The URL is the web page the user is viewing (used to create links to the same page with different GET args)
    :param task_id:
        Show the job tree descending from a particular task.
    :param job_name:
        Filter the task tree in the database by job name.
    :param max_depth:
        Maximum depth of the task tree to descend to.
    :param running_only:
        If true, we only show tree to currently running tasks
    :param include_recent:
        If true, and we're showing running tasks, then also include recently-finished tasks
    :return:
        List[Dict]
    """

    # Start building a list of lines of output
    output: List[Dict] = []

    # Sanitise input
    if task_id is None or task_id < 1:
        task_id = None

    # Fetch list of lines of output we should produce
    if not running_only:
        output_lines = render_task_tree.fetch_job_tree(parent_id=task_id, job_name=job_name, max_depth=max_depth)
    else:
        output_lines = render_task_tree.fetch_running_job_tree(job_name=job_name,
                                                               max_depth=max_depth,
                                                               include_recently_finished=include_recent)

    # Add additional fields to each line of output that are required by the HTML page template
    for item in output_lines:
        # Add an HTML class to colour-code this item based on its status
        html_class = 'waiting'
        if item['d'] > 0:
            html_class = 'done'
        elif item['r'] > 0:
            html_class = 'running'
        elif item['s'] > 0:
            html_class = 'stalled'
        elif item['w'] > 0:
            html_class = 'queued'

        # Indent each item with arrows depending on its depth in the hierarchy
        item['indent'] = " &rarr; " * item['level']
        item['class'] = html_class

        # Create an HTML link which can be used to view deeper into the nested hierarchy of tasks
        if item['tree_truncated']:
            get_args = {'task_id': item['task_id']}
            if job_name is not None:
                get_args['job_name'] = job_name
            if max_depth is not None:
                get_args['max_depth'] = max_depth
            item['more_link'] = "{}?{}".format(self_url, urlencode(get_args))

        output.append(item)

    # Return results
    return output
