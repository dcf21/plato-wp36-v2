# -*- coding: utf-8 -*-
# task_database.py

"""
Module for reading and writing task objects to the database.
"""

import hashlib
import logging
import os
import re
import shutil
import time
import json

from typing import Dict, List, Optional

from .connect_db import DatabaseConnector
from .settings import Settings
from .task_objects import MetadataItem, FileProduct, FileProductVersion, TaskExecutionAttempt, Task
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
        """
        Destructor
        """
        self.close_db()

    def commit(self):
        """
        Commit changes to the database.
        """
        self.db.commit()

    def close_db(self):
        """
        Close database connection.
        """
        if self.db is not None:
            self.db.close()
            self.db = None

    # *** Functions relating to task type lists
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
FROM eas_task_types;""")

        for item in self.conn.fetchall():
            container_list = json.loads(item['workerContainers'])
            output.task_list[item['taskName']] = container_list

            for container_name in container_list:
                output.container_names.add(container_name)

                if container_name not in output.container_capabilities:
                    output.container_capabilities[container_name] = set()

                output.container_capabilities[container_name].add(item['taskName'])

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

    def task_list_fetch_id(self, task_name: str):
        """
        Fetch the integer ID associated with a type of pipeline task.

        :param task_name:
            The name of the pipeline task type.
        :return:
            Integer ID
        """
        self.conn.execute("SELECT taskTypeId FROM eas_task_types WHERE taskName=%s;", (task_name,))
        results = self.conn.fetchall()

        # Check that task is recognised
        assert len(results) == 1, "Unrecognised task type <{}>".format(task_name)

        # Return ID
        return results[0]['taskTypeId']

    # *** Functions relating to metadata items
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
                           product_id: Optional[int] = None,
                           product_version_id: Optional[int] = None):
        """
        Fetch dictionary of metadata objects associated with an entity in the database. Specify *either* a task,
        *or* an execution attempt, *or* an intermediate file product, *or* a file version.

        :param task_id:
            Fetch metadata associated with a particular task.
        :param scheduling_attempt_id:
            Fetch metadata associated with a particular task execution attempt.
        :param product_id:
            Fetch metadata associated with a particular intermediate file product.
        :param product_version_id:
            Fetch metadata associated with a particular version of an intermediate file product.
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
        if product_version_id is not None:
            constraints.append("productVersionId={:d}".format(int(product_version_id)))

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
                            product_id: Optional[int] = None,
                            product_version_id: Optional[int] = None):
        """
        Fetch dictionary of metadata objects associated with an entity in the database. Specify *either* a task,
        *or* an execution attempt, *or* an intermediate file product, *or* a file version.

        :param keyword:
            String metadata keyword
        :param task_id:
            Fetch metadata associated with a particular task.
        :param scheduling_attempt_id:
            Fetch metadata associated with a particular task execution attempt.
        :param product_id:
            Fetch metadata associated with a particular intermediate file product.
        :param product_version_id:
            Fetch metadata associated with a particular version of an intermediate file product.
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
        if product_version_id is not None:
            constraints.append("productVersionId={:d}".format(int(product_version_id)))

        # Fetch metadata from database
        self.conn.execute("""
SELECT k.name AS keyword, m.valueFloat, m.valueString, m.setAtTime
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
                          metadata: Dict[str, MetadataItem],
                          task_id: Optional[int] = None,
                          scheduling_attempt_id: Optional[int] = None,
                          product_id: Optional[int] = None,
                          product_version_id: Optional[int] = None):
        """
        Write a dictionary of metadata objects associated with an entity in the database. Specify *either* a task,
        *or* an execution attempt, *or* an intermediate file product, *or* a file version.

        :param task_id:
            Register metadata associated with a particular task.
        :param scheduling_attempt_id:
            Register metadata associated with a particular task execution attempt.
        :param product_id:
            Register metadata associated with a particular intermediate file product.
        :param product_version_id:
            Fetch metadata associated with a particular version of an intermediate file product.
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
                                                      product_version_id=product_version_id,
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
REPLACE INTO eas_metadata_item
    (taskId, schedulingAttemptId, productId, productVersionId, metadataKey, valueFloat, valueString)
VALUES (%s, %s, %s, %s, %s, %s, %s);
""", (task_id, scheduling_attempt_id, product_id, product_version_id, key_id, value_float, value_string))

    # *** Functions relating to intermediate file product versions
    def file_version_path_for_id(self, product_version_id: int, full_path: bool = True, must_exist: bool = False):
        """
        Get the file system path for a given file product version ID.

        :param int product_version_id:
            ID of a file (which may or may not exist, this method doesn't check)
        :param full_path:
            If true, we return the full path of file products. Otherwise, the path relative to the file
            repository root.
        :param must_exist:
            If true, we only return a file path if the file actually exists
        :return:
            System file path for the file, or None if there is no match
        """

        # Look up file repository filename
        self.conn.execute("""
SELECT v.repositoryId, p.directoryName
FROM eas_product_version v
INNER JOIN eas_product p on v.productId = p.productId
WHERE v.productVersionId = %s;
""", (product_version_id,))
        result = self.conn.fetchall()
        if len(result) != 1:
            return None

        # Path of the file product relative to the file repository root.
        path_string = os.path.join(result[0]['directoryName'], result[0]['repositoryId'])

        # Convert to absolute path
        full_path_string = os.path.join(self.file_store_path, path_string)

        # If user specified that the file must exist, but it does not, we return None
        if must_exist and not os.path.exists(full_path_string):
            return None

        return full_path_string if full_path else path_string

    def file_version_exists_in_db(self, product_version_id: int):
        """
        Check for the presence of the given file_id.

        :param int product_version_id:
            ID of a file
        :return:
            True if we have a record with this ID, False otherwise
        """
        self.conn.execute('SELECT 1 FROM eas_product_version WHERE productVersionId = %s;', (product_version_id,))
        return len(self.conn.fetchall()) > 0

    def file_version_exists_in_file_system(self, product_version_id: int):
        """
        Check for the presence of the given file_id.

        :param int product_version_id:
            ID of a file
        :return:
            True if we have a file in the file system with this ID, False otherwise
        """
        file_path = self.file_version_path_for_id(product_version_id=product_version_id, full_path=True)
        return os.path.isfile(path=file_path)

    def file_version_delete(self, product_version_id: int):
        """
        Delete an intermediate file product version.

        :param int product_version_id:
            ID of a file
        :return:
            None
        """
        file_path = self.file_version_path_for_id(product_version_id=product_version_id, full_path=True)
        try:
            os.unlink(file_path)
        except OSError:
            logging.warning("Could not delete file <{}>".format(file_path))
            pass
        self.conn.execute('DELETE FROM eas_product_version WHERE productVersionId = %s;', (product_version_id,))

    def file_version_lookup(self, product_version_id: int):
        """
        Retrieve a FileProductVersion object representing a file product in the database

        :param int product_version_id:
            ID of a file
        :return:
            A :class:`FileProduct` instance, or None if not found
        """

        # Look up file version properties
        self.conn.execute("""
SELECT productVersionId, productId, generatedByTaskExecution, repositoryId,
       createdTime, modifiedTime, fileMD5, fileSize, passedQc
FROM eas_product_version v
WHERE productVersionId = %s;
""", (product_version_id,))
        result = self.conn.fetchall()

        # Return None if no match
        if len(result) != 1:
            return None

        # Read file metadata
        metadata = self.metadata_fetch_all(product_version_id=result[0]['productVersionId'])

        # Build FileProductVersion instance
        return FileProductVersion(
            product_version_id=result[0]['productVersionId'],
            product_id=result[0]['productId'],
            generated_by_task_execution=result[0]['generatedByTaskExecution'],
            repository_id=result[0]['repositoryId'],
            created_time=result[0]['createdTime'],
            modified_time=result[0]['modifiedTime'],
            file_md5=result[0]['fileMD5'],
            file_size=result[0]['fileSize'],
            passed_qc=result[0]['passed_qc'],
            metadata=metadata
        )

    @staticmethod
    def file_version_get_md5_hash(file_path):
        """
        Calculate the MD5 checksum for a file on disk.

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
    def file_version_get_hash(timestamp, filename, *file_info_fields):
        """
        Get a random hexadecimal hash for a file product, used when storing it on disk to avoid clashes with other
        files with the same filename.

        :param timestamp:
            Unix time associated with the file.
        :param filename:
            Filename of the file (used to determine the file type suffix)
        :param file_info_fields:
            An arbitrary list of string fields which are used to generate a unique hash for this file
        :return:
            Hash string
        """
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

    def file_version_register(self, product_id: int,
                              generated_by_task_execution: int,
                              file_path_input: str,
                              preserve: bool = False,
                              created_time: Optional[float] = None,
                              modified_time: Optional[float] = None,
                              passed_qc: Optional[bool] = None,
                              metadata: Dict[str, MetadataItem] = None):
        """
        Register a file product in the database, and move it into our file archive

        :param product_id:
            The integer ID of the intermediate file product of which this file is a version.
        :param generated_by_task_execution:
            The integer ID of the task execution attempt which generated this file.
        :param file_path_input:
            The path to where a copy of this file can be found (usually in a temporary file system)
        :param preserve:
            Boolean flag indicating whether the input file should be left in situ (copied into the archive), or removed
            (moved into the archive).
        :param created_time:
            The time when this file product was created by the pipeline
        :param modified_time:
            The time when this file product was modified by the pipeline
        :param passed_qc:
            Boolean indicating whether QC checks have taken place on this file, and whether they passed
        :param metadata:
            Dictionary of metadata associated with this file product
        :return:
            Integer ID for this file product
        """

        # Look up information about file product
        file_product_obj = self.file_product_lookup(product_id=product_id)

        # Has a file been supplied?
        if not os.path.exists(file_path_input):
            raise ValueError('No file exists at <{}>'.format(file_path_input))

        # Get checksum for file, and size
        file_size_bytes = os.stat(file_path_input).st_size
        file_md5 = self.file_version_get_md5_hash(file_path=file_path_input)

        # Set creation time, if it is not manually specified
        if created_time is None:
            created_time = time.time()
        if modified_time is None:
            modified_time = time.time()

        # Pick a repositoryId for this file
        repository_fname = self.file_version_get_hash(created_time, file_product_obj.filename,
                                                      product_id, time.time())

        # Insert record into the database
        self.conn.execute("""
INSERT INTO eas_product_version
    (productId, generatedByTaskExecution, repositoryId, createdTime, modifiedTime,
     fileMD5, fileSize, passedQc)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
""",
                          (product_id, generated_by_task_execution, repository_fname,
                           created_time, modified_time,
                           file_md5, file_size_bytes, passed_qc))
        product_version_id = self.conn.lastrowid

        # Physically move file into our file archive
        target_file_directory = os.path.join(self.file_store_path, file_product_obj.directory)
        os.makedirs(name=target_file_directory, mode=0o755, exist_ok=True)

        target_file_path = os.path.join(target_file_directory, repository_fname)
        try:
            if preserve:
                shutil.copy(file_path_input, target_file_path)
            else:
                shutil.move(file_path_input, target_file_path)
        except OSError:
            logging.error("Could not move file <{}> into repository".format(repository_fname))

        # Register file metadata
        if metadata is not None:
            self.metadata_register(product_version_id=product_version_id, metadata=metadata)

        # Return integer product version id
        return product_version_id

    def file_version_update(self, product_version_id: int,
                            file_path_input: str,
                            preserve: bool = False,
                            modified_time: Optional[float] = None,
                            passed_qc: Optional[bool] = None,
                            metadata: Dict[str, MetadataItem] = None):
        """
        Update information about a file product in the database

        :param product_version_id:
            The ID integer of the file product version to update.
        :param file_path_input:
            The path to where a copy of this file can be found (usually in a temporary file system)
        :param preserve:
            Boolean flag indicating whether the input file should be left in situ (copied into the archive), or removed
            (moved into the archive).
        :param modified_time:
            The time when this file product was modified by the pipeline
        :param passed_qc:
            Boolean indicating whether QC checks have taken place on this file, and whether they passed
        :param metadata:
            Dictionary of metadata associated with this file product version
        :return:
            None
        """

        # Look up information about existing file
        target_file_path = self.file_version_path_for_id(product_version_id=product_version_id,
                                                         full_path=True, must_exist=False)
        old_file_exists = os.path.exists(target_file_path)

        # Has a new file been supplied?
        if file_path_input is not None:
            # Check that file exists
            if not os.path.exists(file_path_input):
                raise ValueError('No file exists at <{}>'.format(file_path_input))

            # Get checksum for file, and size
            file_size_bytes = os.stat(file_path_input).st_size
            file_md5 = self.file_version_get_md5_hash(file_path=file_path_input)

            # Set new modification time, if it is not manually specified
            if modified_time is None:
                modified_time = time.time()

            # Physically move file into the file archive
            target_file_directory = os.path.split(target_file_path)[0]
            os.makedirs(name=target_file_directory, mode=0o755, exist_ok=True)

            try:
                if preserve:
                    shutil.copy(file_path_input, target_file_path)
                else:
                    shutil.move(file_path_input, target_file_path)
            except OSError:
                logging.error("Could not move file <{}> into repository".format(target_file_path))

            # Update database information about the file
            self.conn.execute("""
UPDATE eas_product_version SET fileMD5=%s, fileSize=%s WHERE productVersionId=%s;
""", (file_md5, file_size_bytes, product_version_id))

        # Update timestamp
        if modified_time is not None:
            self.conn.execute("""
UPDATE eas_product_version SET modifiedTime=%s WHERE productVersionId=%s;
""", (modified_time, product_version_id))

        # Update remaining fields
        if passed_qc is not None:
            self.conn.execute("""
UPDATE eas_product_version SET passedQc=%s WHERE productVersionId=%s;
""", (passed_qc, product_version_id))

        # Register file metadata
        if metadata is not None:
            self.metadata_register(product_version_id=product_version_id, metadata=metadata)

    # *** Functions relating to intermediate file products
    def file_product_exists_in_db(self, product_id: int):
        """
        Check for the presence of the given intermediate file product.

        :param int product_id:
            The file ID
        :return:
            True if we have a record with this ID, False otherwise
        """
        self.conn.execute('SELECT 1 FROM eas_product WHERE productId = %s;', (product_id,))
        return len(self.conn.fetchall()) > 0

    def file_product_has_been_created(self, product_id: int):
        """
        Check for the presence of the given file_id.

        :param int product_id:
            The file ID
        :return:
            True if we have a file in the file system with this ID, False otherwise
        """
        self.conn.execute('SELECT 1 FROM eas_product_version WHERE productId = %s;', (product_id,))
        return len(self.conn.fetchall()) > 0

    def file_product_has_passed_qc(self, product_id: int):
        """
        Check for the presence of the given file_id.

        :param int product_id:
            The file ID
        :return:
            True if we have a file in the file system with this ID, False otherwise
        """
        self.conn.execute('SELECT 1 FROM eas_product_version WHERE productId = %s AND passedQc;', (product_id,))
        return len(self.conn.fetchall()) > 0

    def file_product_delete(self, product_id: int):
        """
        Delete an intermediate file product.

        :param int product_id:
            The file ID
        :return:
            None
        """
        self.conn.execute('SELECT productVersionId FROM eas_product_version WHERE productId = %s;', (product_id,))
        file_product_versions = self.conn.fetchall()

        for item in file_product_versions:
            self.file_version_delete(product_version_id=item['productVersionId'])

        self.conn.execute('DELETE FROM eas_product WHERE productId = %s', (product_id,))

    def file_product_lookup(self, product_id: int):
        """
        Retrieve a FileProduct object representing a file product in the database

        :param int product_id:
            The file ID
        :return:
            A :class:`FileProduct` instance, or None if not found
        """

        # Look up file product properties
        self.conn.execute("""
SELECT productId, generatorTask, plannedTime, directoryName, filename, mimeType,
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
            generator_task=result[0]['generatorTask'],
            planned_time=result[0]['plannedTime'],
            directory=result[0]['directoryName'],
            filename=result[0]['filename'],
            semantic_type=result[0]['semanticType'],
            mime_type=result[0]['mimeType'],
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

    def file_product_register(self, generator_task: int, directory: str, filename: str,
                              semantic_type: str,
                              planned_time: Optional[float] = None,
                              mime_type: Optional[str] = None,
                              metadata: Dict[str, MetadataItem] = None):
        """
        Register a file product in the database, and move it into our file archive

        :param generator_task:
            The ID integer of the pipeline task which generates this file product.
        :param directory:
            The directory in the file repository to place this file product into
        :param filename:
            The filename of this file product
        :param semantic_type:
            The name used to identify the type of data in this file, e.g. "lightcurve" or "periodogram".
            Each file output from any given pipeline step must have a unique semantic type.
        :param planned_time:
            The time when the pipeline scheduler created a database entry for this file product
        :param mime_type:
            The mime type of this file, used so a web interface can serve it if needed
        :param metadata:
            Dictionary of metadata associated with this file product
        :return:
            Integer ID for this file product
        """
        if planned_time is None:
            planned_time = time.time()

        # Get ID code for obs_type
        semantic_type_id = self.semantic_type_get_id(semantic_type)

        # Insert record into the database
        self.conn.execute("""
INSERT INTO eas_product (generatorTask, plannedTime, directoryName, filename, semanticType, mimeType)
VALUES (%s, %s, %s, %s, %s, %s);
""",
                          (generator_task, planned_time, directory, filename, semantic_type_id, mime_type))
        product_id = self.conn.lastrowid

        # Register file metadata
        if metadata is not None:
            self.metadata_register(product_id=product_id, metadata=metadata)

        # Return integer product id
        return product_id

    def file_product_update(self, product_id: int,
                            planned_time: Optional[float] = None,
                            mime_type: Optional[str] = None,
                            metadata: Dict[str, MetadataItem] = None):
        """
        Update information about a file product in the database

        :param product_id:
            The ID integer of the file product to update.
        :param planned_time:
            The time when the pipeline scheduler created a database entry for this file product
        :param mime_type:
            The mime type of this file, used so a web interface can serve it if needed
        :param metadata:
            Dictionary of metadata associated with this file product
        :return:
            None
        """

        # Update timestamps
        if planned_time is not None:
            self.conn.execute("UPDATE eas_product SET plannedTime=%s WHERE productId=%s", (planned_time, product_id))

        # Update remaining fields
        if mime_type is not None:
            self.conn.execute("UPDATE eas_product SET mimeType=%s WHERE productId=%s", (mime_type, product_id))

        # Register file metadata
        if metadata is not None:
            self.metadata_register(product_id=product_id, metadata=metadata)

    # *** Functions relating to execution attempts
    def execution_attempt_exists_in_db(self, attempt_id: int):
        """
        Check for the presence of the given task execution attempt.

        :param int attempt_id:
            The attempt ID
        :return:
            True if we have a record with this ID, False otherwise
        """
        self.conn.execute('SELECT 1 FROM eas_scheduling_attempt WHERE schedulingAttemptId = %s;', (attempt_id,))
        return len(self.conn.fetchall()) > 0

    def execution_attempt_delete(self, attempt_id: int):
        """
        Delete a scheduling attempt.

        :param int attempt_id:
            The execution attempt ID
        :return:
            None
        """

        # Delete file products
        self.conn.execute('SELECT productVersionId FROM eas_product_version WHERE generatedByTaskExecution = %s;',
                          (attempt_id,))
        file_product_versions = self.conn.fetchall()

        for item in file_product_versions:
            self.file_version_delete(product_version_id=item['productVersionId'])

        # Delete execution attempt
        self.conn.execute('DELETE FROM eas_scheduling_attempt WHERE schedulingAttemptId = %s', (attempt_id,))

    def execution_attempt_fetch_output_files(self, attempt_id: int):
        """
        Retrieve a dictionary of all the files generated by a task execution attempt, indexed by their
        semantic types.

        :param attempt_id:
            The ID of the task execution attempt.
        :return:
            Dictionary of :class:`FileProductVersion`, indexed by semantic type string.
        """

        output: Dict[str, FileProductVersion] = {}

        # Look up all the file products generated by this task execution attempt
        self.conn.execute("""
SELECT v.productVersionId, s.name AS semanticType
FROM eas_product_version v
INNER JOIN eas_product p ON p.productId = v.productId
INNER JOIN eas_semantic_type s ON s.semanticTypeId = p.semanticType
WHERE generatedByTaskExecution = %s;
""", (attempt_id,))
        file_product_versions = self.conn.fetchall()

        for item in file_product_versions:
            output[item['semanticType']] = self.file_version_lookup(product_version_id=item['productVersionId'])

        return output

    def execution_attempt_lookup(self, attempt_id: int):
        """
        Retrieve a TaskExecutionAttempt object representing a task execution attempt in the database

        :param int attempt_id:
            The execution attempt ID
        :return:
            A :class:`TaskExecutionAttempt` instance, or None if not found
        """

        # Look up execution attempt properties
        self.conn.execute("""
SELECT schedulingAttemptId, taskId, queuedTime, startTime, latestHeartbeat, endTime,
       allProductsPassedQc, errorFail, errorText,
       runTimeWallClock, runTimeCpu, runTimeCpuIncChildren
FROM eas_scheduling_attempt a
WHERE schedulingAttemptId = %s;
""", (attempt_id,))
        result = self.conn.fetchall()

        # Return None if no match
        if len(result) != 1:
            return None

        # List output file products
        output_files = self.execution_attempt_fetch_output_files(
            attempt_id=result[0]['schedulingAttemptId']
        )

        # Read scheduling attempt metadata
        metadata = self.metadata_fetch_all(scheduling_attempt_id=result[0]['schedulingAttemptId'])

        # Build TaskExecutionAttempt instance
        return TaskExecutionAttempt(
            attempt_id=result[0]['schedulingAttemptId'],
            task_id=result[0]['taskId'],
            queued_time=result[0]['queuedTime'],
            start_time=result[0]['startTime'],
            latest_heartbeat_time=result[0]['latestHeartbeat'],
            end_time=result[0]['endTime'],
            all_products_passed_qc=result[0]['allProductsPassedQc'],
            error_fail=result[0]['errorFail'],
            error_text=result[0]['errorText'],
            run_time_wall_clock=result[0]['runTimeWallClock'],
            run_time_cpu=result[0]['runTimeCpu'],
            run_time_cpu_inc_children=result[0]['runTimeCpuIncChildren'],
            metadata=metadata,
            output_files=output_files
        )

    def execution_attempt_register(self, task_id: Optional[int] = None,
                                   queued_time: Optional[float] = None,
                                   metadata: Optional[Dict[str, MetadataItem]] = None):
        """
        Register an attempt to execute a task in the database

        :param task_id:
            The integer ID of the task which is being run in the <eas_tasks> table
        :param queued_time:
            The unix timestamp when this execution attempt was put into the job queue
        :return:
            Integer ID for this execution attempt
        """
        if queued_time is None:
            queued_time = time.time()

        # Insert record into the database
        self.conn.execute("""
INSERT INTO eas_scheduling_attempt (taskId, queuedTime)
VALUES (%s, %s);
""", (task_id, queued_time))
        output_id = self.conn.lastrowid

        # Register execution attempt metadata
        if metadata is not None:
            self.metadata_register(scheduling_attempt_id=output_id, metadata=metadata)

        # Return integer id
        return output_id

    def execution_attempt_update(self, attempt_id: Optional[int] = None,
                                 queued_time: Optional[float] = None,
                                 start_time: Optional[float] = None,
                                 latest_heartbeat_time: Optional[float] = None,
                                 end_time: Optional[float] = None,
                                 all_products_passed_qc: Optional[bool] = None,
                                 error_fail: Optional[bool] = None, error_text: Optional[str] = None,
                                 run_time_wall_clock: Optional[float] = None,
                                 run_time_cpu: Optional[float] = None,
                                 run_time_cpu_inc_children: Optional[float] = None,
                                 metadata: Optional[Dict[str, MetadataItem]] = None):
        """
        Update information about a task execution attempt in the database

        :param attempt_id:
            The integer ID of this task execution attempt.
        :param queued_time:
            The unix timestamp when this execution attempt was put into the job queue
        :param start_time:
            The unix timestamp when this execution attempt began to be executed
        :param latest_heartbeat_time:
            The unix timestamp when this execution attempt last sent a heartbeat message
        :param end_time:
            The unix timestamp when this execution attempt signaled that it had completed
        :param all_products_passed_qc:
            A boolean flag indicating whether all the file products from this execution attempt passed
            their QC inspection.
        :param error_fail:
            A boolean flag indicating whether this execution attempt signalled that an error occurred
        :param error_text:
            The error message text associated with any failure of this job
        :param run_time_wall_clock:
            The number of seconds the job took to execute, in wall clock time
        :param run_time_cpu:
            The number of seconds the job took to execute, in CPU time
        :param run_time_cpu_inc_children:
            The number of seconds the job took to execute, in CPU time, including child threads
        :param metadata:
            A dictionary of metadata associated with this execution attempt.
        :return:
            None
        """

        # Update timestamps
        if queued_time is not None:
            self.conn.execute("UPDATE eas_scheduling_attempt SET queuedTime=%s WHERE schedulingAttemptId=%s",
                              (queued_time, attempt_id))
        if start_time is not None:
            self.conn.execute("UPDATE eas_scheduling_attempt SET startTime=%s WHERE schedulingAttemptId=%s",
                              (start_time, attempt_id))
        if latest_heartbeat_time is not None:
            self.conn.execute("UPDATE eas_scheduling_attempt SET latestHeartbeat=%s WHERE schedulingAttemptId=%s",
                              (latest_heartbeat_time, attempt_id))
        if end_time is not None:
            self.conn.execute("UPDATE eas_scheduling_attempt SET endTime=%s WHERE schedulingAttemptId=%s",
                              (end_time, attempt_id))

        # Update remaining fields
        if all_products_passed_qc is not None:
            self.conn.execute("UPDATE eas_scheduling_attempt SET allProductsPassedQc=%s WHERE schedulingAttemptId=%s",
                              (all_products_passed_qc, attempt_id))
        if error_fail is not None:
            self.conn.execute("UPDATE eas_scheduling_attempt SET errorFail=%s WHERE schedulingAttemptId=%s",
                              (error_fail, attempt_id))
        if error_text is not None:
            self.conn.execute("UPDATE eas_scheduling_attempt SET errorText=%s WHERE schedulingAttemptId=%s",
                              (error_text, attempt_id))
        if run_time_wall_clock is not None:
            self.conn.execute("UPDATE eas_scheduling_attempt SET runTimeWallClock=%s WHERE schedulingAttemptId=%s",
                              (run_time_wall_clock, attempt_id))
        if run_time_cpu is not None:
            self.conn.execute("UPDATE eas_scheduling_attempt SET runTimeCpu=%s WHERE schedulingAttemptId=%s",
                              (run_time_cpu, attempt_id))
        if run_time_cpu_inc_children is not None:
            self.conn.execute("UPDATE eas_scheduling_attempt SET runTimeCpuIncChildren=%s WHERE schedulingAttemptId=%s",
                              (run_time_cpu_inc_children, attempt_id))

        # Register execution attempt metadata
        if metadata is not None:
            self.metadata_register(scheduling_attempt_id=attempt_id, metadata=metadata)

    # *** Functions relating to tasks
    def task_exists_in_db(self, task_id: int):
        """
        Check for the presence of the given task.

        :param int task_id:
            The task ID
        :return:
            True if we have a record with this ID, False otherwise
        """
        self.conn.execute('SELECT 1 FROM eas_task WHERE taskId = %s;', (task_id,))
        return len(self.conn.fetchall()) > 0

    def task_delete(self, task_id: int):
        """
        Delete a task.

        :param int task_id:
            The task ID
        :return:
            None
        """

        # Delete any execution attempts
        self.conn.execute('SELECT schedulingAttemptId FROM eas_scheduling_attempt WHERE taskId = %s;',
                          (task_id,))
        execution_attempts = self.conn.fetchall()

        for item in execution_attempts:
            self.execution_attempt_delete(attempt_id=item['schedulingAttemptId'])

        # Delete task
        self.conn.execute('DELETE FROM eas_task WHERE taskId = %s', (task_id,))

    def task_fetch_file_products(self, task_id: int):
        """
        Retrieve a dictionary of all the file products generated by a task, indexed by their
        semantic types.

        :param task_id:
            The ID of the task.
        :return:
            Dictionary of :class:`FileProduct`, indexed by semantic type string.
        """

        output: Dict[str, FileProduct] = {}

        # Look up all the file products generated by this task execution attempt
        self.conn.execute("""
SELECT p.productId, s.name AS semanticType
FROM eas_product p
INNER JOIN eas_semantic_type s ON s.semanticTypeId = p.semanticType
WHERE generatorTask = %s;
""", (task_id,))
        file_products = self.conn.fetchall()

        for item in file_products:
            output[item['semanticType']] = self.file_product_lookup(product_id=item['productId'])

        return output

    def task_fetch_file_inputs(self, task_id: int):
        """
        Retrieve a dictionary of all the file inputs to a task, indexed by their
        semantic types.

        :param task_id:
            The ID of the task.
        :return:
            Dictionary of :class:`FileProduct`, indexed by semantic type string.
        """

        output: Dict[str, FileProduct] = {}

        # Look up all the file products generated by this task execution attempt
        self.conn.execute("""
SELECT p.inputId, s.name AS semanticType
FROM eas_task_input p
INNER JOIN eas_semantic_type s ON s.semanticTypeId = p.semanticType
WHERE generatorTask = %s;
""", (task_id,))
        file_products = self.conn.fetchall()

        for item in file_products:
            output[item['semanticType']] = self.file_product_lookup(product_id=item['inputId'])

        return output

    def task_fetch_execution_attempts(self, task_id: int, successful: Optional[bool] = None):
        """
        Retrieve a dictionary of all the attempts to execute a task, indexed by their integer UIDs

        :param task_id:
            The ID of the task.
        :param successful:
            Boolean indicating whether we're searching for successful executions, incomplete executions, or both
        :return:
            Dictionary of :class:`TaskExecutionAttempt`, indexed by unique ID.
        """

        output: Dict[str, TaskExecutionAttempt] = {}

        # Compile constraints
        constraint = "1"
        if type(successful) == bool:
            if successful:
                constraint = "allProductsPassedQc"
            else:
                constraint = "NOT allProductsPassedQc"

        # Look up all the file products generated by this task execution attempt
        self.conn.execute("""
SELECT s.schedulingAttemptId
FROM eas_scheduling_attempt s
WHERE taskId = %s AND {};
""".format(constraint), (task_id,))
        execution_attempts = self.conn.fetchall()

        for item in execution_attempts:
            output[item['schedulingAttemptId']] = self.execution_attempt_lookup(
                attempt_id=item['schedulingAttemptId']
            )

        return output

    def task_lookup(self, task_id: int):
        """
        Retrieve a Task object representing a task in the database

        :param int task_id:
            The task ID
        :return:
            A :class:`Task` instance, or None if not found
        """

        # Look up task properties
        self.conn.execute("""
SELECT taskId, parentTask, createdTime, t.taskName AS taskTypeName, jobName, workingDirectory
FROM eas_task j
INNER JOIN eas_task_types t ON t.taskTypeId = j.taskTypeId
WHERE taskId = %s;
""", (task_id,))
        result = self.conn.fetchall()

        # Return None if no match
        if len(result) != 1:
            return None

        # List input file products
        input_products = self.task_fetch_file_inputs(
            task_id=result[0]['taskId']
        )

        # List output file products
        output_products = self.task_fetch_file_products(
            task_id=result[0]['taskId']
        )

        # Read scheduling attempt metadata
        metadata = self.metadata_fetch_all(task_id=result[0]['taskId'])

        # List successfully completed execution attempts
        execution_attempts_passed = self.task_fetch_execution_attempts(
            task_id=result[0]['taskId'], successful=True)

        # List incomplete execution attempts
        execution_attempts_incomplete = self.task_fetch_execution_attempts(
            task_id=result[0]['taskId'], successful=False)

        # Build Task instance
        return Task(
            task_id=result[0]['taskId'],
            parent_id=result[0]['parentTask'],
            created_time=result[0]['createdTime'],
            task_type=result[0]['taskTypeName'],
            job_name=result[0]['jobName'],
            working_directory=result[0]['workingDirectory'],
            input_files=input_products,
            execution_attempts_passed=execution_attempts_passed,
            execution_attempts_incomplete=execution_attempts_incomplete,
            metadata=metadata,
            output_products=output_products
        )

    def task_register(self, parent_id: Optional[int] = None,
                      created_time: Optional[float] = None,
                      task_type: Optional[str] = None, job_name: Optional[str] = None,
                      working_directory: Optional[str] = None,
                      input_files: Optional[Dict[str, FileProduct]] = None,
                      metadata: Dict[str, MetadataItem] = None):
        """
        Register a new task in the database

        :param parent_id:
            The integer ID of the parent task which may have spawned this sub-task
            (e.g. a task execution chain)
        :param created_time:
            The unix timestamp when this task was created
        :param task_type:
            The string name of this type of task, as defined in <task_type_registry.xml>
        :param job_name:
            The human-readable name of the top-level job (requested by a user) that this task of part of
        :param working_directory:
            The directory in the file store where this job should write its output file products
        :param input_files:
            The list of file products that this task uses as inputs. This task cannot be executed
            until all of these file products exist and have passed QC.
        :param metadata:
            A dictionary of metadata associated with this task
        :return:
            Integer ID for this task
        """
        if created_time is None:
            created_time = time.time()
        if working_directory is None:
            working_directory = ""

        # Fetch task type integer id
        task_type_id = self.task_list_fetch_id(task_name=task_type)

        # Insert record into the database
        self.conn.execute("""
INSERT INTO eas_task (parentTask, createdTime, taskTypeId, jobName, workingDirectory)
VALUES (%s, %s, %s, %s, %s);
""", (parent_id, created_time, task_type_id, job_name, working_directory))
        output_id = self.conn.lastrowid

        # Register task metadata
        if metadata is not None:
            self.metadata_register(task_id=output_id, metadata=metadata)

        # Register task input files
        if input_files is not None:
            for semantic_type, input_file in input_files.items():
                semantic_type_id = self.semantic_type_get_id(name=semantic_type)
                self.conn.execute("""
REPLACE INTO eas_task_input (taskId, inputId, semanticType) VALUES (%s, %s, %s);
""", (output_id, input_file.product_id, semantic_type_id))

        # Return integer id
        return output_id

    def task_update(self, task_id: Optional[int] = None,
                    metadata: Dict[str, MetadataItem] = None):
        """
        Update information about a task in the database

        :param task_id:
            The integer ID of this task.
        :param metadata:
            A dictionary of metadata associated with this task.
        :return:
            None
        """

        # Register task metadata
        if metadata is not None:
            self.metadata_register(task_id=task_id, metadata=metadata)