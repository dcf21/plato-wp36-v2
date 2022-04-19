# -*- coding: utf-8 -*-
# task_objects.py

"""
Pythonic objects to represent pipeline task entries in the database
"""

import time

from typing import Dict, List, Optional


class MetadataItem:
    """
    A class representing a metadata value to associate with an item.
    """

    def __init__(self, keyword: str, value, timestamp=None):
        # Default creation time
        if timestamp is None:
            timestamp = time.time()

        # Initialise null item
        self.keyword = keyword
        self.value = value
        self.timestamp = timestamp

    def as_dict(self):
        """
        Turn a class instance into a Python dictionary, allowing it to be transmitted in JSON format.
        :return:
            Dict
        """
        return {"keyword": self.keyword,
                "value": self.value,
                "timestamp": self.timestamp
                }

    @classmethod
    def from_dict(cls, d: Dict):
        """
        Recreate a class instance from a Python dictionary, allowing it to be transmitted in JSON format.
        :param d:
            Dictionary representation of class instance
        :return:
            Class instance
        """
        return cls(keyword=d['keyword'],
                   value=d['value'],
                   timestamp=d['timestamp']
                   )


class FileProduct:
    """
    Python class to represent an intermediate file product, each associated with the task which generated / will
    generate them. Note that multiple versions of the same file product may exist on disk, if a task runs multiple
    times.
    """

    def __init__(self, **kwargs):
        # Initialise null intermediate file product
        self.product_id: Optional[int] = None
        self.generator_task: Optional[int] = None
        self.planned_time: Optional[float] = None
        self.directory: Optional[str] = None
        self.filename: Optional[str] = None
        self.semantic_type: Optional[str] = None
        self.mime_type: Optional[str] = None
        self.metadata: Dict[str, MetadataItem] = {}

        # Configure intermediate file product
        self.configure(**kwargs)

    def configure(self, product_id: Optional[int] = None,
                  generator_task: Optional[int] = None,
                  planned_time: Optional[float] = None,
                  directory: Optional[str] = None, filename: Optional[str] = None,
                  semantic_type: Optional[str] = None, mime_type: Optional[str] = None,
                  metadata: Dict[str, MetadataItem] = None):
        """
        :param product_id:
            The ID integer for this file product in the database.
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
            None
        """
        if product_id is not None:
            self.product_id = product_id
        if generator_task is not None:
            self.generator_task = generator_task
        if planned_time is not None:
            self.planned_time = planned_time
        if directory is not None:
            self.directory = directory
        if filename is not None:
            self.filename = filename
        if semantic_type is not None:
            self.semantic_type = semantic_type
        if mime_type is not None:
            self.mime_type = mime_type
        if metadata is not None:
            # Merge new metadata with existing metadata
            for item in metadata.values():
                self.metadata[item.keyword] = item

    def set_metadata(self, keyword: str, value):
        """
        Set an item of metadata associated with this object.

        :param keyword:
            Metadata keyword
        :param value:
            Metadata value
        :return:
            None
        """

        if not isinstance(value, MetadataItem):
            value = MetadataItem(keyword=keyword, value=value)
        value.keyword = keyword
        self.metadata[keyword] = value

    def as_dict(self):
        """
        Turn a class instance into a Python dictionary, allowing it to be transmitted in JSON format.
        :return:
            Dict
        """
        return {
            "product_id": self.product_id,
            "generator_task": self.generator_task,
            "planned_time": self.planned_time,
            "directory": self.directory,
            "filename": self.filename,
            "semantic_type": self.semantic_type,
            "mime_type": self.mime_type,
            "metadata": [item.as_dict() for item in self.metadata.values()]
        }

    @classmethod
    def from_dict(cls, d: Dict):
        """
        Recreate a class instance from a Python dictionary, allowing it to be transmitted in JSON format.
        :param d:
            Dictionary representation of class instance
        :return:
            Class instance
        """

        # Create class instance
        output = cls(
            product_id=d['product_id'],
            generator_task=d['generator_task'],
            planned_time=d['planned_time'],
            directory=d['directory'],
            filename=d['filename'],
            semantic_type=d['semantic_type'],
            mime_type=d['mime_type'],
        )

        # Populate metadata
        for item in d['metadata']:
            item_object = MetadataItem.from_dict(item)
            output.configure(metadata={item_object.keyword: item_object})

        # Return output
        return output


class FileProductVersion:
    """
    Python class to represent a version of an intermediate file product. Multiple versions of the same file product
    may exist on disk, if a task runs multiple times.
    """

    def __init__(self, **kwargs):
        # Initialise null intermediate file product version
        self.product_version_id: Optional[int] = None
        self.product_id: Optional[int] = None
        self.generated_by_task_execution: Optional[int] = None
        self.repository_id: Optional[str] = None
        self.created_time: Optional[float] = None
        self.modified_time: Optional[float] = None
        self.file_md5: Optional[str] = None
        self.file_size: Optional[int] = None
        self.passed_qc: Optional[bool] = None
        self.metadata: Dict[str, MetadataItem] = {}

        # Configure intermediate file product version
        self.configure(**kwargs)

    def configure(self, product_version_id: Optional[int] = None,
                  product_id: Optional[int] = None,
                  generated_by_task_execution: Optional[int] = None,
                  repository_id: Optional[str] = None,
                  created_time: Optional[float] = None,
                  modified_time: Optional[float] = None,
                  file_md5: Optional[str] = None, file_size: Optional[int] = None,
                  passed_qc: Optional[bool] = None,
                  metadata: Dict[str, MetadataItem] = None):
        """
        :param product_version_id:
            The integer ID of this version of a file product
        :param product_id:
            The integer ID of the intermediate file product of which this file is a version.
        :param generated_by_task_execution:
            The integer ID of the task execution attempt which generated this file.
        :param created_time:
            The time when this file product was created by the pipeline
        :param modified_time:
            The time when this file product was modified by the pipeline
        :param passed_qc:
            Boolean indicating whether QC checks have taken place on this file, and whether they passed
        :param metadata:
            Dictionary of metadata associated with this file product
        :param repository_id:
            The string filename used to store this file in the file store.
        :param file_md5:
            The MD5 hash of the file
        :param file_size:
            The number of bytes in the file
        :return:
            None
        """
        if product_version_id is not None:
            self.product_version_id = product_version_id
        if product_id is not None:
            self.product_id = product_id
        if generated_by_task_execution is not None:
            self.generated_by_task_execution = generated_by_task_execution
        if repository_id is not None:
            self.repository_id = repository_id
        if created_time is not None:
            self.created_time = created_time
        if modified_time is not None:
            self.modified_time = modified_time
        if file_md5 is not None:
            self.file_md5 = file_md5
        if file_size is not None:
            self.file_size = file_size
        if passed_qc is not None:
            self.passed_qc = passed_qc
        if metadata is not None:
            # Merge new metadata with existing metadata
            for item in metadata.values():
                self.metadata[item.keyword] = item

    def set_metadata(self, keyword: str, value):
        """
        Set an item of metadata associated with this object.

        :param keyword:
            Metadata keyword
        :param value:
            Metadata value
        :return:
            None
        """

        if not isinstance(value, MetadataItem):
            value = MetadataItem(keyword=keyword, value=value)
        value.keyword = keyword
        self.metadata[keyword] = value

    def as_dict(self):
        """
        Turn a class instance into a Python dictionary, allowing it to be transmitted in JSON format.
        :return:
            Dict
        """
        return {
            "product_version_id": self.product_version_id,
            "product_id": self.product_id,
            "generated_by_task_execution": self.generated_by_task_execution,
            "repository_id": self.repository_id,
            "created_time": self.created_time,
            "modified_time": self.modified_time,
            "file_md5": self.file_md5,
            "file_size": self.file_size,
            "passed_qc": self.passed_qc,
            "metadata": [item.as_dict() for item in self.metadata.values()]
        }

    @classmethod
    def from_dict(cls, d: Dict):
        """
        Recreate a class instance from a Python dictionary, allowing it to be transmitted in JSON format.
        :param d:
            Dictionary representation of class instance
        :return:
            Class instance
        """

        # Create class instance
        output = cls(
            product_version_id=d['product_version_id'],
            product_id=d['product_id'],
            generated_by_task_execution=d['generated_by_task_execution'],
            repository_id=d['repository_id'],
            created_time=d['created_time'],
            modified_time=d['modified_time'],
            file_md5=d['file_md5'],
            file_size=d['file_size'],
            passed_qc=d['passed_qc']
        )

        # Populate metadata
        for item in d['metadata']:
            item_object = MetadataItem.from_dict(item)
            output.configure(metadata={item_object.keyword: item_object})

        # Return output
        return output


class TaskExecutionAttempt:
    """
    Python class to represent an attempt to execute a pipeline task.
    """

    def __init__(self, **kwargs):
        # Initialise null task execution attempt
        self.attempt_id: Optional[int] = None
        self.task_id: Optional[int] = None
        self.queued_time: Optional[float] = None
        self.start_time: Optional[float] = None
        self.latest_heartbeat_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.all_products_passed_qc: Optional[bool] = None
        self.error_fail: Optional[bool] = None
        self.error_text: Optional[str] = None
        self.run_time_wall_clock: Optional[float] = None
        self.run_time_cpu: Optional[float] = None
        self.run_time_cpu_inc_children: Optional[float] = None
        self.metadata: Dict[str, MetadataItem] = {}
        self.output_files: Dict[str, FileProductVersion] = {}

        # Configure task execution attempt
        self.configure(**kwargs)

    def configure(self, attempt_id: Optional[int] = None, task_id: Optional[int] = None,
                  queued_time: Optional[float] = None,
                  start_time: Optional[float] = None,
                  latest_heartbeat_time: Optional[float] = None,
                  end_time: Optional[float] = None,
                  all_products_passed_qc: Optional[bool] = None,
                  error_fail: Optional[bool] = None, error_text: Optional[str] = None,
                  run_time_wall_clock: Optional[float] = None,
                  run_time_cpu: Optional[float] = None,
                  run_time_cpu_inc_children: Optional[float] = None,
                  metadata: Optional[Dict[str, MetadataItem]] = None,
                  output_files: Optional[Dict[str, FileProductVersion]] = None):
        """
        :param attempt_id:
            The integer ID of this task execution attempt.
        :param task_id:
            The integer ID of the task which is being run in the <eas_tasks> table
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
        :param output_files:
            A dictionary of the output file products from this execution attempt, represented by
            FileProductVersion objects.
        :return:
            None
        """
        if attempt_id is not None:
            self.attempt_id = attempt_id
        if task_id is not None:
            self.task_id = task_id
        if queued_time is not None:
            self.queued_time = queued_time
        if start_time is not None:
            self.start_time = start_time
        if latest_heartbeat_time is not None:
            self.latest_heartbeat_time = latest_heartbeat_time
        if end_time is not None:
            self.end_time = end_time
        if all_products_passed_qc is not None:
            self.all_products_passed_qc = all_products_passed_qc
        if error_fail is not None:
            self.error_fail = error_fail
        if error_text is not None:
            self.error_text = error_text
        if run_time_wall_clock is not None:
            self.run_time_wall_clock = run_time_wall_clock
        if run_time_cpu is not None:
            self.run_time_cpu = run_time_cpu
        if run_time_cpu_inc_children is not None:
            self.run_time_cpu_inc_children = run_time_cpu_inc_children
        if metadata is not None:
            # Merge new metadata with existing metadata
            for item in metadata.values():
                self.metadata[item.keyword] = item
        if output_files is not None:
            # Merge new output files with existing ones
            for semantic_type, item in output_files.items():
                self.output_files[semantic_type] = item

    def set_metadata(self, keyword: str, value):
        """
        Set an item of metadata associated with this object.

        :param keyword:
            Metadata keyword
        :param value:
            Metadata value
        :return:
            None
        """

        if not isinstance(value, MetadataItem):
            value = MetadataItem(keyword=keyword, value=value)
        value.keyword = keyword
        self.metadata[keyword] = value

    def as_dict(self):
        """
        Turn a class instance into a Python dictionary, allowing it to be transmitted in JSON format.
        :return:
            Dict
        """
        return {
            "attempt_id": self.attempt_id,
            "task_id": self.task_id,
            "queued_time": self.queued_time,
            "start_time": self.start_time,
            "latest_heartbeat_time": self.latest_heartbeat_time,
            "end_time": self.end_time,
            "all_products_passed_qc": self.all_products_passed_qc,
            "error_fail": self.error_fail,
            "error_text": self.error_text,
            "run_time_wall_clock": self.run_time_wall_clock,
            "run_time_cpu": self.run_time_cpu,
            "run_time_cpu_inc_children": self.run_time_cpu_inc_children,
            "metadata": [item.as_dict() for item in self.metadata.values()],
            "output_files": [(keyword, item.as_dict()) for keyword, item in self.output_files.items()]
        }

    @classmethod
    def from_dict(cls, d: Dict):
        """
        Recreate a class instance from a Python dictionary, allowing it to be transmitted in JSON format.
        :param d:
            Dictionary representation of class instance
        :return:
            Class instance
        """

        # Create class instance
        output = cls(
            attempt_id=d['attempt_id'],
            task_id=d['task_id'],
            queued_time=d['queued_time'],
            start_time=d['start_time'],
            latest_heartbeat_time=d['latest_heartbeat_time'],
            end_time=d['end_time'],
            all_products_passed_qc=d['all_products_passed_qc'],
            error_fail=d['error_fail'],
            error_text=d['error_text'],
            run_time_wall_clock=d['run_time_wall_clock'],
            run_time_cpu=d['run_time_cpu'],
            run_time_cpu_inc_children=d['run_time_cpu_inc_children']
        )

        # Populate metadata
        for item in d['metadata']:
            item_object = MetadataItem.from_dict(item)
            output.configure(metadata={item_object.keyword: item_object})

        # Populate output files
        for item in d['output_files']:
            output.configure(output_files={item[0]: FileProductVersion.from_dict(item[1])})

        # Return output
        return output


class Task:
    """
    Python class to represent a task in the <eas_task> database table.
    """

    def __init__(self, **kwargs):
        # Initialise null task
        self.task_id: Optional[int] = None
        self.parent_id: Optional[int] = None
        self.created_time: Optional[float] = None
        self.task_type: Optional[str] = None
        self.job_name: Optional[str] = None
        self.working_directory: Optional[str] = None
        self.input_files: Dict[str, FileProduct] = {}
        self.execution_attempts_passed: Dict[int, TaskExecutionAttempt] = {}
        self.execution_attempts_incomplete: Dict[int, TaskExecutionAttempt] = {}
        self.metadata: Dict[str, MetadataItem] = {}
        self.output_files: Dict[str, FileProduct] = {}

        # Configure task
        self.configure(**kwargs)

    def configure(self, task_id: Optional[int] = None, parent_id: Optional[int] = None,
                  created_time: Optional[float] = None,
                  task_type: Optional[str] = None, job_name: Optional[str] = None,
                  working_directory: Optional[str] = None,
                  input_files: Optional[Dict[str, FileProduct]] = None,
                  execution_attempts_passed: List[TaskExecutionAttempt] = None,
                  execution_attempts_incomplete: List[TaskExecutionAttempt] = None,
                  metadata: Dict[str, MetadataItem] = None,
                  output_files: Optional[Dict[str, FileProduct]] = None):
        """
        :param task_id:
            The integer ID of this task in the <eas_task> table
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
        :param execution_attempts_passed:
            A list of all the successfully completed attempts to execute this task
        :param execution_attempts_incomplete:
            A list of all the failed, or incomplete, attempts to execute this task
        :param metadata:
            A dictionary of metadata associated with this task
        :param output_files:
            A list of all the file products that this task will create, or has created
        :return:
            None
        """
        if task_id is not None:
            self.task_id = task_id
        if parent_id is not None:
            self.parent_id = parent_id
        if created_time is not None:
            self.created_time = created_time
        if task_type is not None:
            self.task_type = task_type
        if job_name is not None:
            self.job_name = job_name
        if working_directory is not None:
            self.working_directory = working_directory
        if input_files is not None:
            # Merge new output files with existing ones
            for semantic_type, item in input_files.items():
                self.input_files[semantic_type] = item
        if execution_attempts_passed is not None:
            # Merge new execution attempts with existing list
            for item in execution_attempts_passed:
                self.execution_attempts_passed[item.attempt_id] = item
        if execution_attempts_incomplete is not None:
            # Merge new execution attempts with existing list
            for item in execution_attempts_incomplete:
                self.execution_attempts_incomplete[item.attempt_id] = item
        if metadata is not None:
            # Merge new metadata with existing metadata
            for item in metadata.values():
                self.metadata[item.keyword] = item
        if output_files is not None:
            # Merge new output files with existing ones
            for semantic_type, item in output_files.items():
                self.output_files[semantic_type] = item

    def set_metadata(self, keyword: str, value):
        """
        Set an item of metadata associated with this object.

        :param keyword:
            Metadata keyword
        :param value:
            Metadata value
        :return:
            None
        """

        if not isinstance(value, MetadataItem):
            value = MetadataItem(keyword=keyword, value=value)
        value.keyword = keyword
        self.metadata[keyword] = value

    def as_dict(self):
        """
        Turn a class instance into a Python dictionary, allowing it to be transmitted in JSON format.
        :return:
            Dict
        """
        return {
            "task_id": self.task_id,
            "parent_id": self.parent_id,
            "created_time": self.created_time,
            "task_type": self.task_type,
            "job_name": self.job_name,
            "working_directory": self.working_directory,
            "input_files": [(keyword, item.as_dict()) for keyword, item in self.input_files.items()],
            "execution_attempts_passed": [item.as_dict() for item in self.execution_attempts_passed.values()],
            "execution_attempts_incomplete": [item.as_dict() for item in self.execution_attempts_incomplete.values()],
            "metadata": [item.as_dict() for item in self.metadata.values()],
            "output_files": [(keyword, item.as_dict()) for keyword, item in self.output_files.items()]
        }

    @classmethod
    def from_dict(cls, d: Dict):
        """
        Recreate a class instance from a Python dictionary, allowing it to be transmitted in JSON format.
        :param d:
            Dictionary representation of class instance
        :return:
            Class instance
        """

        # Create class instance
        output = cls(
            task_id=d['task_id'],
            parent_id=d['parent_id'],
            created_time=d['created_time'],
            task_type=d['task_type'],
            job_name=d['job_name'],
            working_directory=d['working_directory']
        )

        # Populate execution attempts
        for item in d['execution_attempts_passed']:
            output.configure(execution_attempts_passed=[TaskExecutionAttempt.from_dict(item)])
        for item in d['execution_attempts_incomplete']:
            output.configure(execution_attempts_incomplete=[TaskExecutionAttempt.from_dict(item)])

        # Populate input files
        for item in d['input_files']:
            output.configure(input_files={item[0]: FileProduct.from_dict(item[1])})

        # Populate output files
        for item in d['output_files']:
            output.configure(output_files={item[0]: FileProduct.from_dict(item[1])})

        # Populate metadata
        for item in d['metadata']:
            item_object = MetadataItem.from_dict(item)
            output.configure(metadata={item_object.keyword: item_object})

        # Return output
        return output
