# -*- coding: utf-8 -*-
# file_explorer.py

from datetime import datetime
from math import ceil
from typing import Dict, List

from plato_wp36 import task_database


def fetch_directory_list(page: int = 1,
                         page_size: int = 100):
    """
    Fetch a list of all the directories in the file system.

    :param page:
        Page number of results.
    :param page_size:
        Size of each page of results.
    :return:
        List[Dict]
    """

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Count number of matching results
        task_db.db_handle.parameterised_query("""
SELECT COUNT(DISTINCT directoryName) AS count
FROM eas_product;
""")

        item_count = int(task_db.db_handle.fetchall()[0]['count'])

        # Work out paging request
        page = int(page)
        page_size = int(page_size)
        result_limit = int(page_size)
        result_offset = (page - 1) * page_size
        if result_offset > item_count:
            page = 1
            result_offset = 0
        page_max = max(1, int(ceil(item_count / page_size)))

        # Search for all directory names
        task_db.db_handle.parameterised_query("""
SELECT directoryName, COUNT(productId) AS count
FROM eas_product 
GROUP BY directoryName
ORDER BY directoryName
LIMIT {limit} OFFSET {offset};
""".format(limit=result_limit, offset=result_offset))

        # Fetch all directory names
        directory_list = task_db.db_handle.fetchall()

        # Start building output
        output_list: List[Dict] = []

        result_min = int(result_offset + 1)
        result_max = int(result_offset + len(directory_list))

        output = {
            'result_count': item_count,
            'result_count_str': "{:,}".format(item_count),
            'result_min': result_min,
            'result_max': result_max,
            'result_min_str': "{:,}".format(result_min),
            'result_max_str': "{:,}".format(result_max),
            'page_number': page,
            'page_max': page_max,
            'show_page_min': max(1, page - 8),
            'show_page_max': min(page_max, page + 7),
            'list': output_list
        }

        # Convert names into dictionaries
        for item in directory_list:
            output_list.append({
                'name': item['directoryName'],
                'item_count': item['count']
            })

    # Return results
    return output


def fetch_file_list(directory: str,
                    page: int = 1,
                    page_size: int = 100):
    """
    Fetch a list of all the files in a directory.

    :param page:
        Page number of results.
    :param page_size:
        Size of each page of results.
    :param directory:
        The directory to list the contents from
    :return:
        List[Dict]
    """

    # Open connection to the database
    with task_database.TaskDatabaseConnection() as task_db:
        # Count number of matching results
        task_db.db_handle.parameterised_query("""
SELECT COUNT(DISTINCT p.filename) AS count
FROM eas_product p
INNER JOIN eas_semantic_type est on p.semanticType = est.semanticTypeId
WHERE p.directoryName=%s;
""", (directory,))

        item_count = int(task_db.db_handle.fetchall()[0]['count'])

        # Work out paging request
        page = int(page)
        page_size = int(page_size)
        result_limit = int(page_size)
        result_offset = (page - 1) * page_size
        if result_offset > item_count:
            page = 1
            result_offset = 0
        page_max = max(1, int(ceil(item_count / page_size)))

        # Search for all filenames
        task_db.db_handle.parameterised_query("""
SELECT DISTINCT p.filename, est.name AS semanticType
FROM eas_product p
INNER JOIN eas_semantic_type est on p.semanticType = est.semanticTypeId
WHERE p.directoryName=%s
ORDER BY p.filename
LIMIT {limit} OFFSET {offset};
""".format(limit=result_limit, offset=result_offset), (directory,))

        # Fetch all intermediate file products
        file_list = task_db.db_handle.fetchall()

        # Start building output
        output_list: List[Dict] = []

        result_min = int(result_offset + 1)
        result_max = int(result_offset + len(file_list))

        output = {
            'result_count': item_count,
            'result_count_str': "{:,}".format(item_count),
            'result_min': result_min,
            'result_max': result_max,
            'result_min_str': "{:,}".format(result_min),
            'result_max_str': "{:,}".format(result_max),
            'page_number': page,
            'page_max': page_max,
            'show_page_min': max(1, page - 8),
            'show_page_max': min(page_max, page + 7),
            'list': output_list
        }

        # Convert names into dictionaries
        for item in file_list:
            version_list = fetch_file_versions(directory=directory, filename=item['filename'])
            output_list.append({
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
                'uid': item['productVersionId'],
                'attempt_id': item['generatedByTaskExecution'],
                'time': datetime.utcfromtimestamp(item['modifiedTime']).strftime('%Y-%m-%d %H:%M:%S'),
                'file_size': item['fileSize'],
                'passed_qc': "&#x2714;" if item['passedQc'] else "&#x274C;"  # tick or cross in HTML
            })

    # Return results
    return output
