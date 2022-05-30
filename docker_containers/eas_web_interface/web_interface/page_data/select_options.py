# -*- coding: utf-8 -*-
# job_names.py

from typing import List

from plato_wp36 import task_database


def job_name_options():
    """
    Fetch list of all job names in the task database

    :return:
        List[str]
    """

    output: List[str] = []

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Search for all job names in the database
        task_db.db_handle.parameterised_query("SELECT DISTINCT jobName FROM eas_task ORDER BY jobName;")

        name_list = task_db.db_handle.fetchall()

        # Add names to output list
        for item in name_list:
            if item['jobName'] is not None:
                output.append(item['jobName'])

    # Return results
    return output


def task_type_options():
    """
    Fetch list of all task type names in the task database

    :return:
        List[str]
    """

    output: List[str] = []

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Search for all job names in the database
        task_db.db_handle.parameterised_query("SELECT DISTINCT taskTypeName FROM eas_task_types ORDER BY taskTypeName;")

        name_list = task_db.db_handle.fetchall()

        # Add names to output list
        for item in name_list:
            output.append(item['taskTypeName'])

    # Return results
    return output
