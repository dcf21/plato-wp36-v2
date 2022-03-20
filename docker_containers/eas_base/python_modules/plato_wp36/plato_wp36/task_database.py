# -*- coding: utf-8 -*-
# task_database.py

"""
Module for reading and writing task objects to the database.
"""

import hashlib
import logging
import os
import re
import time
import json

from typing import Dict, List, Optional, Set

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
    def metadata_keyword_id(self, keyword: str):
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

    def metadata_fetch_all(self,
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
SELECT k.name AS keyword, m.valueFloat, m.valueString, m.setAtTime
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
            output[item['keyword']] = MetadataItem(keyword=item['keyword'],
                                                   value=value,
                                                   timestamp=item['setAtTime'])

        # Return dictionary of <MetadataItem>s
        return output

    def metadata_fetch_item(self, keyword: str,
                            task_id: Optional[int] = None,
                            scheduling_attempt_id: Optional[int] = None,
                            product_id: Optional[int] = None):
        """
        Fetch dictionary of metadata objects associated with an item.

        :param keyword:
            String metadata keyword
        :param task_id:
            Fetch metadata associated with a particular task.
        :param scheduling_attempt_id:
            Fetch metadata associated with a particular task execution attempt.
        :param product_id:
            Fetch metadata associated with a particular intermediate file product
        :return:
            Dictionary of MetadataItem objects
        """

        # Look up numerical ID of metadata key
        key_id = self.metadata_keyword_id(keyword)

        # Build list of SQL constraints
        constraints = ["m.metadataKey={:d}".format(key_id)]

        if task_id is not None:
            constraints.append("taskId={:d}".format(int(task_id)))
        if scheduling_attempt_id is not None:
            constraints.append("schedulingAttemptId={:d}".format(int(scheduling_attempt_id)))
        if product_id is not None:
            constraints.append("productId={:d}".format(int(product_id)))

        # Fetch metadata from database
        self.conn.execute("""
SELECT k.name AS keyword, m.valueFloat, m.valueString, m.setAtTime, 
FROM eas_metadata_item m
INNER JOIN eas_metadata_keys k ON k.keyId=m.metadataKey
WHERE {};""".format(" AND ".join(constraints)))

        # Create a dictionary from database results
        output = None

        for item in self.conn.fetchall():
            value = None
            for value_field in ('valueString', 'valueFloat'):
                if item[value_field]:
                    value = item[value_field]
            output = MetadataItem(keyword=item['keyword'],
                                  value=value,
                                  timestamp=item['setAtTime'])

        # Return <MetadataItem>
        return output

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
            key_id = self.metadata_keyword_id(item.keyword)
            value_float = None
            value_string = None

            # Fetch existing metadata value
            existing_value = self.metadata_fetch_item(keyword=item.keyword,
                                                      task_id=task_id, product_id=product_id,
                                                      scheduling_attempt_id=scheduling_attempt_id)

            # No action required if new value equals old value
            if item.value == existing_value:
                continue

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
    def file_product_path_for_id(self, product_id: int, full_path: bool = True):
        """
        Get the file system path for a given product file ID. Does not guarantee that the file exists.

        :param int product_id:
            ID of a file (which may or may not exist, this method doesn't check)
        :param full_path:
            If true, we return the full path of file products. Otherwise, the path relative to the file
            repository root.
        :return:
            System file path for the file, or None if there is no match
        """

        # Look up file repository filename
        self.conn.execute("SELECT repositoryId, directory FROM eas_product WHERE productId = %s;", (product_id,))
        result = self.conn.fetchall()
        if len(result) != 1:
            return None

        # Path of the file product relative to the file repository root.
        path = os.path.join(result[0]['directory'], result[0]['repositoryId'])

        # If requested, convert to absolute path
        if full_path:
            path = os.path.join(self.file_store_path, path)

        return path

    def file_product_exists_in_db(self, product_id: int):
        """
        Check for the presence of the given file_id.

        :param int product_id:
            The file ID
        :return:
            True if we have a record with this ID, False otherwise
        """
        self.conn.execute('SELECT 1 FROM eas_product WHERE productId = %s', (product_id,))
        return len(self.conn.fetchall()) > 0

    def file_product_exists_in_file_system(self, product_id: int):
        """
        Check for the presence of the given file_id.

        :param int product_id:
            The file ID
        :return:
            True if we have a file in the file system with this ID, False otherwise
        """
        file_path = self.file_product_path_for_id(product_id=product_id, full_path=True)
        return os.path.isfile(path=file_path)

    def file_product_delete(self, product_id: int):
        """
        Delete an intermediate file product.

        :param int product_id:
            The file ID
        :return:
            None
        """
        file_path = self.file_product_path_for_id(product_id=product_id, full_path=True)
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
SELECT productId, repositoryId, generatorTask, plannedTime, createdTime, modifiedTime,
       directory, filename, mimeType, created, passedQc,
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
        metadata = self.metadata_fetch_all(product_id=result[0]['productId'])

        # Build FileProduct instance
        return FileProduct(
            product_id=result[0]['productId'],
            repository_id=result[0]['repositoryId'],
            generator_task=result[0]['generatorTask'],
            planned_time=result[0]['plannedTime'],
            created_time=result[0]['createdTime'],
            modified_time=result[0]['modifiedTime'],
            directory=result[0]['directory'],
            filename=result[0]['filename'],
            semantic_type=result[0]['semanticType'],
            mime_type=result[0]['mimeType'],
            created=result[0]['created'],
            passed_qc=result[0]['passed_qc'],
            metadata=metadata
        )

    def semantic_type_get_id(self, name: str):
        """
        Fetch the numerical ID associated with a semantic type name.

        :param name:
            String semantic type
        :return:
            Integer ID
        """

        while True:
            # Lookup ID from database
            self.conn.execute("SELECT semanticTypeId FROM eas_semantic_type WHERE name=%s;", (name,))

            result = self.conn.fetchall()
            if len(result) > 0:
                return result[0]['semanticTypeId']

            # Create new ID
            self.conn.execute("INSERT INTO eas_semantic_type (name) VALUES (%s);", (name,))

    @staticmethod
    def file_get_md5_hash(file_path):
        """
        Calculate the MD5 checksum for a file.

        :param string file_path:
            Path to the file
        :return:
            MD5 checksum
        """
        checksum = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(128 * checksum.block_size), b''):
                checksum.update(chunk)
        return checksum.hexdigest()

    @staticmethod
    def file_product_get_hash(timestamp, filename, *file_info_fields):
        time_string = time.strftime("%Y%m%d_%H%M%S", time.gmtime(timestamp))
        key_string = "_".join([str(item) for item in file_info_fields])
        uid = hashlib.md5(key_string.encode()).hexdigest()

        # Preserve file extension, so file type is obvious
        test = re.match(".*(\.[^.]*)", filename)
        if not (test is None):
            suffix = test.group(1)
            output = ("{}_{}".format(time_string, uid))[0:32 - len(suffix)] + suffix
        else:
            output = ("{}_{}".format(timestamp, uid))[0:32]

        return output

    def file_product_register(self, generator_task: int, directory: str, filename: str,
                              file_path_input: str,
                              semantic_type: str,
                              planned_time: Optional[float] = None,
                              created_time: Optional[float] = None,
                              modified_time: Optional[float] = None,
                              mime_type: Optional[str] = None,
                              passed_qc: Optional[bool] = None,
                              metadata: List[MetadataItem] = None):
        if metadata is None:
            metadata = []
        if planned_time is None:
            planned_time = time.time()

        # Has a file been supplied?
        if file_path_input is not None:
            # Check that file exists
            if not os.path.exists(file_path_input):
                raise ValueError('No file exists at {0}'.format(file_path_input))

            # Get checksum for file, and size
            file_size_bytes = os.stat(file_path_input).st_size
            file_md5 = self.file_get_md5_hash(file_path_input)
            created = True
        else:
            file_size_bytes = None
            file_md5 = None
            created = False

        # Pick a repositoryId for this file
        repository_fname = self.file_product_get_hash(planned_time, filename, generator_task,
                                                      semantic_type, time.time())

        # Get ID code for obs_type
        semantic_type_id = self.semantic_type_get_id(semantic_type)

        # Insert record into the database
        self.conn.execute("""
INSERT INTO eas_product (repositoryId, generatorTask, plannedTime, createdTime, modifiedTime,
                         directory, filename, semanticType, mimeType, created, passedQc)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
""",
                          (repository_fname, generator_task, planned_time, created_time, modified_time,
                           directory, filename, semantic_type_id, mime_type,
                           created, passed_qc))

        # Register file metadata