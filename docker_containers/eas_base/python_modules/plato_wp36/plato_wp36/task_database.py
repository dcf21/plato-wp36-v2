# -*- coding: utf-8 -*-
# task_database.py

"""
Module for reading and writing task objects to the database.
"""

import logging
import os
import json

from typing import Dict, Optional, Set

from .connect_db import DatabaseConnector
from .settings import Settings
from .task_objects import MetadataItem, FileProduct, TaskExecutionAttempt, Task
from .task_types import TaskTypeList


class TaskDatabaseConnection:
    """
    Class for reading and writing task objects to the database.
    """

    def __init__(self, file_store_path: Optional[str] = None):
        """
        Initialise a database connection
        """

        # Null database connection (so destructor doesn't fail if we never open database)
        self.db = None

        # Fetch testbench settings
        self.settings = Settings().settings

        # If file store path is not specified, use default
        if file_store_path is None:
            file_store_path = self.settings['dataPath']

        # Path to where we store all our intermediate file products
        self.file_store_path = file_store_path

        # Open connection to the database
        self.db_connector = DatabaseConnector()
        self.db, self.conn = self.db_connector.connect_db()

    def __del__(self):
        self.close_db()

    def commit(self):
        self.db.commit()

    def close_db(self):
        if self.db is not None:
            self.db.close()
            self.db = None

    # Functions relating to task type lists
    def task_list_from_db(self):
        """
        Return a list of all known task names, from the database.

        :return:
            List of all known task names.
        """

        # Create empty task list
        output = TaskTypeList()

        # Fetch list of tasks
        self.conn.execute("""
SELECT taskTypeId, taskName, workerContainers
FROM eas_task_types""")

        for item in self.conn.fetchall():
            output.task_list[item['taskName']] = json.loads(item['workerContainers'])

        # Return list
        return output

    def task_list_to_db(self, task_list: TaskTypeList):
        """
        Write a list of all known task names to the database.

        :return:
            None
        """

        # Write each task type in turn
        for name, containers in task_list.task_list.items():
            self.conn.execute("""
REPLACE INTO eas_task_types (taskName, workerContainers) VALUES (%s, %s);
""", (name, json.dumps(list(containers))))

    # Functions relating to metadata items
    def metadata_fetch(self,
                       task_id: Optional[int] = None,
                       scheduling_attempt_id: Optional[int] = None,
                       product_id: Optional[int] = None):
        """
        Fetch dictionary of metadata objects associated with an item.

        :param task_id:
            Fetch metadata associated with a particular task.
        :param scheduling_attempt_id:
            Fetch metadata associated with a particular task execution attempt.
        :param product_id:
            Fetch metadata associated with a particular intermediate file product
        :return:
            Dictionary of MetadataItem objects
        """

        # Build list of SQL constraints
        constraints = []

        if task_id is not None:
            constraints.append("taskId={:d}".format(int(task_id)))
        if scheduling_attempt_id is not None:
            constraints.append("schedulingAttemptId={:d}".format(int(scheduling_attempt_id)))
        if product_id is not None:
            constraints.append("productId={:d}".format(int(product_id)))

        # Fetch metadata from database
        self.conn.execute("""
SELECT k.name AS keyword, m.valueFloat, m.valueString
FROM eas_metadata_item m
INNER JOIN eas_metadata_keys k ON k.keyId=m.metadataKey
WHERE {};""".format(" AND ".join(constraints)))

        # Create a dictionary from database results
        output = {}

        for item in self.conn.fetchall():
            value = None
            for value_field in ('valueString', 'valueFloat'):
                if item[value_field]:
                    value = item[value_field]
            output[item['keyword']] = MetadataItem(keyword=item['keyword'], value=value)

        # Return dictionary of <MetadataItem>s
        return output

    def metadata_key_id(self, keyword: str):
        """
        Fetch the numerical ID associated with a metadata keyword.

        :param keyword:
            String metadata keyword
        :return:
            Integer ID
        """

        while True:
            # Lookup ID from database
            self.conn.execute("SELECT keyId FROM eas_metadata_keys WHERE name=%s;", (keyword,))

            result = self.conn.fetchall()
            if len(result) > 0:
                return result[0]['keyId']

            # Create new ID
            self.conn.execute("INSERT INTO eas_metadata_keys (name) VALUES (%s);", (keyword,))

    def metadata_register(self,
                          task_id: Optional[int], scheduling_attempt_id: Optional[int], product_id: Optional[int],
                          metadata: Dict[str, MetadataItem]):
        """
        Write a dictionary of metadata objects associated with an item.

        :param task_id:
            Register metadata associated with a particular task.
        :param scheduling_attempt_id:
            Register metadata associated with a particular task execution attempt.
        :param product_id:
            Register metadata associated with a particular intermediate file product
        :param metadata:
            Dictionary of <MetadataItem>s
        :return:
            None
        """

        for item in metadata.values():
            key_id = self.metadata_key_id(item.keyword)
            value_float = None
            value_string = None

            # Work out whether metadata is float-like or string-like
            try:
                value_float = float(item.value)
            except ValueError:
                value_string = str(item.value)

            # Write metadata to the database
            self.conn.execute("""
REPLACE INTO eas_metadata_item (taskId, schedulingAttemptId, productId, metadataKey, valueFloat, valueString)
VALUES (%s, %s, %s, %s, %s, %s);
""", (task_id, scheduling_attempt_id, product_id, key_id, value_float, value_string))

    # Functions relating to intermediate file products
    def file_product_path_for_id(self, product_id: int):
        """
        Get the file system path for a given product file ID. Does not guarantee that the file exists.

        :param int product_id:
            ID of a file (which may or may not exist, this method doesn't check)
        :return:
            System file path for the file
        """

        # Look up file repository filename
        self.conn.execute("SELECT repositoryId, directory FROM eas_product WHERE productId = %s;", (product_id,))
        result = self.conn.fetchall()
        assert len(result) == 1

        return os.path.join(self.file_store_path, result[0]['directory'], result[0]['repositoryId'])

    def file_product_exists(self, product_id: int):
        """
        Check for the presence of the given file_id.

        :param int product_id:
            The file ID
        :return:
            True if we have a record with this ID, False otherwise
        """
        self.conn.execute('SELECT 1 FROM eas_product WHERE productId = %s', (product_id,))
        return len(self.conn.fetchall()) > 0

    def file_product_delete(self, product_id: int):
        """
        Delete an intermediate file product.

        :param int product_id:
            The file ID
        :return:
            None
        """
        file_path = self.file_product_path_for_id(product_id=product_id)
        try:
            os.unlink(file_path)
        except OSError:
            logging.warning("Could not delete file <{}>".format(file_path))
            pass
        self.conn.execute('DELETE FROM eas_product WHERE productId = %s', (product_id,))

    def file_product_lookup(self, product_id: int):
        """
        Retrieve a FileProduct object representing a file product in the database

        :param int product_id:
            The file ID
        :return:
            A :class:`FileProduct` instance, or None if not found
        """

        # Look up file repository filename
        self.conn.execute("""
SELECT productId, repositoryId, generatorTask, directory, filename, semanticType, created, passedQc,
       s.name AS semanticType
FROM eas_product p
INNER JOIN eas_semantic_type s ON s.semanticTypeId=p.semanticType
WHERE productId = %s;
""", (product_id,))
        result = self.conn.fetchall()

        # Return None if no match
        if len(result) != 1:
            return None

        # Read file metadata
        metadata = self.metadata_fetch(product_id=result[0]['productId'])

        # Build FileProduct instance
        return FileProduct(
            product_id=result[0]['productId'],
            repository_id=result[0]['repositoryId'],
            generator_task=result[0]['generatorTask'],
            directory=result[0]['directory'],
            filename=result[0]['filename'],
            semantic_type=result[0]['semanticType'],
            created=result[0]['created'],
            passed_qc=result[0]['passed_qc'],
            metadata=metadata
        )
