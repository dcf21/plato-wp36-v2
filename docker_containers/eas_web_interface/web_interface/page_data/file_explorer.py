# -*- coding: utf-8 -*-
# file_explorer.py

from datetime import datetime

from typing import Dict, List

from plato_wp36 import task_database


def fetch_directory_list():
    """
    Fetch a list of all the directories in the file system.

    :return:
        List[Dict]
    """

    output: List[Dict] = []

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Search for all directory names
        task_db.db_handle.parameterised_query("""
SELECT DISTINCT p.directoryName
FROM eas_product p
ORDER BY p.directoryName;
""")

        # Fetch all directory names
        directory_list = task_db.db_handle.fetchall()

        # Convert names into dictionaries
        for item in directory_list:
            output.append({
                'name': item['directoryName']
            })

    # Return results
    return output


def fetch_file_list(directory: str):
    """
    Fetch a list of all the files in a directory.

    :param directory:
        The directory to list the contents from
    :return:
        List[Dict]
    """

    output: List[Dict] = []

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Search for all filenames
        task_db.db_handle.parameterised_query("""
SELECT DISTINCT p.filename, est.name AS semanticType
FROM eas_product p
INNER JOIN eas_semantic_type est on p.semanticType = est.semanticTypeId
WHERE p.directoryName=%s
ORDER BY p.filename;
""", (directory,))

        # Fetch all intermediate file products
        file_list = task_db.db_handle.fetchall()

        # Convert names into dictionaries
        for item in file_list:
            version_list = fetch_file_versions(directory=directory, filename=item['filename'])
            output.append({
                'name': item['filename'],
                'type': item['semanticType'],
                'versions': version_list
            })

    # Return results
    return output


def fetch_file_versions(directory: str, filename: str):
    """
    Fetch a list of all the versions of a particular intermediate file product

    :param directory:
        The directory containing the file product
    :param filename:
        The filename of the file product
    :return:
        List[Dict]
    """

    output: List[Dict] = []

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Search for all filenames
        task_db.db_handle.parameterised_query("""
SELECT v.productVersionId, v.generatedByTaskExecution, v.modifiedTime, v.fileSize, v.passedQc
FROM eas_product_version v
INNER JOIN eas_product p on v.productId = p.productId
WHERE p.directoryName=%s AND p.filename=%s
ORDER BY v.generatedByTaskExecution;
""", (directory, filename))

        # Fetch all versions of this file products
        file_list = task_db.db_handle.fetchall()

        # Convert items into dictionaries
        for item in file_list:
            output.append({
                'attempt_id': item['generatedByTaskExecution'],
                'time': datetime.utcfromtimestamp(item['modifiedTime']).strftime('%Y-%m-%d %H:%M:%S'),
                'file_size': item['fileSize'],
                'passed_qc': "&#x2714;" if item['passedQc'] else "&#x274C;"  # tick or cross in HTML
            })

    # Return results
    return output
