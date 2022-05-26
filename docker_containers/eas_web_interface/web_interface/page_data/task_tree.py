# -*- coding: utf-8 -*-
# task_tree.py

from typing import Dict, List, Optional

from plato_wp36.diagnostics import render_task_tree


def fetch_job_tree(job_name: Optional[str] = None, status: str = 'any', max_depth: Optional[int] = None):
    """
    Fetch the hierarchy of jobs in the database.

    :param job_name:
        Filter the task tree in the database by job name.
    :param status:
        Filter the task tree by job status.
    :param max_depth:
        Maximum depth of the task tree to descend to.
    :return:
        List[Dict]
    """

    output: List[Dict] = []

    def add_tree_item(item: Dict):
        html_class = 'waiting'
        if item['d'] > 0:
            html_class = 'done'
        elif item['r'] > 0:
            html_class = 'running'
        elif item['s'] > 0:
            html_class = 'stalled'
        elif item['w'] > 0:
            html_class = 'queued'

        item['indent'] = " &rarr; " * item['level']
        item['class'] = html_class

        output.append(item)

    render_task_tree.fetch_job_tree(
        renderer=add_tree_item,
        job_name=job_name,
        status=status,
        max_depth=max_depth
    )

    # Return results
    return output
