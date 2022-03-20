# -*- coding: utf-8 -*-
# task_objects.py

"""
Pythonic objects to represent pipeline task entries in the database
"""

import time

from typing import Dict, List, Optional, Set


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
    Python class to represent an intermediate file product.
    """

    def __init__(self, **kwargs):
        # Initialise null task
        self.product_id: Optional[int] = None
        self.repository_id: Optional[str] = None
        self.generator_task: Optional[int] = None
        self.planned_time: Optional[float] = None
        self.created_time: Optional[float] = None
        self.modified_time: Optional[float] = None
        self.file_md5: Optional[str] = None
        self.file_size: Optional[int] = None
        self.directory: Optional[str] = None
        self.filename: Optional[str] = None
        self.semantic_type: Optional[str] = None
        self.mime_type: Optional[str] = None
        self.created: Optional[bool] = None
        self.passed_qc: Optional[bool] = None
        self.metadata: Dict[str, MetadataItem] = {}

        # Configure task
        self.configure(**kwargs)

    def configure(self, product_id: Optional[int] = None, repository_id: Optional[str] = None,
                  generator_task: Optional[int] = None,
                  planned_time: Optional[float] = None,
                  created_time: Optional[float] = None,
                  modified_time: Optional[float] = None,
                  file_md5: Optional[str] = None, file_size: Optional[int] = None,
                  directory: Optional[str] = None, filename: Optional[str] = None,
                  semantic_type: Optional[str] = None, mime_type: Optional[str] = None,
                  created: Optional[bool] = None, passed_qc: Optional[bool] = None,
                  metadata: Dict[str, MetadataItem] = None):
        if product_id is not None:
            self.product_id = product_id
        if repository_id is not None:
            self.repository_id = repository_id
        if generator_task is not None:
            self.generator_task = generator_task
        if planned_time is not None:
            self.planned_time = planned_time
        if created_time is not None:
            self.created_time = created_time
        if modified_time is not None:
            self.modified_time = modified_time
        if file_md5 is not None:
            self.file_md5 = file_md5
        if file_size is not None:
            self.file_size = file_size
        if directory is not None:
            self.directory = directory
        if filename is not None:
            self.filename = filename
        if semantic_type is not None:
            self.semantic_type = semantic_type
        if mime_type is not None:
            self.mime_type = mime_type
        if created is not None:
            self.created = created
        if passed_qc is not None:
            self.passed_qc = passed_qc
        if metadata is not None:
            # Merge new metadata with existing metadata
            for item in metadata.values():
                self.metadata[item.keyword] = item

    def as_dict(self):
        """
        Turn a class instance into a Python dictionary, allowing it to be transmitted in JSON format.
        :return:
            Dict
        """
        return {"product_id": self.product_id,
                "repository_id": self.repository_id,
                "generator_task": self.generator_task,
                "planned_time": self.planned_time,
                "created_time": self.created_time,
                "modified_time": self.modified_time,
                "file_md5": self.file_md5,
                "file_size": self.file_size,
                "directory": self.directory,
                "filename": self.filename,
                "semantic_type": self.semantic_type,
                "mime_type": self.mime_type,
                "created": self.created,
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
        output = cls(product_id=d['product_id'],
                     repository_id=d['repository_id'],
                     generator_task=d['generator_task'],
                     planned_time=d['planned_time'],
                     created_time=d['created_time'],
                     modified_time=d['modified_time'],
                     file_md5=d['file_md5'],
                     file_size=d['file_size'],
                     directory=d['directory'],
                     filename=d['filename'],
                     semantic_type=d['semantic_type'],
                     mime_type=d['mime_type'],
                     created=d['created'],
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
        # Initialise null task
        self.attempt_id: Optional[int] = None
        self.task_id: Optional[int] = None
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.all_products_passed_qc: Optional[bool] = None
        self.error_fail: Optional[bool] = None
        self.error_text: Optional[str] = None
        self.run_time_wall_clock: Optional[float] = None
        self.run_time_cpu: Optional[float] = None
        self.run_time_cpu_inc_children: Optional[float] = None
        self.metadata: Dict[str, MetadataItem] = {}
        self.output_files: Set[int] = set()

        # Configure task
        self.configure(**kwargs)

    def configure(self, attempt_id: Optional[int] = None, task_id: Optional[int] = None,
                  start_time: Optional[float] = None, end_time: Optional[float] = None,
                  all_products_passed_qc: Optional[bool] = None,
                  error_fail: Optional[bool] = None, error_text: Optional[str] = None,
                  run_time_wall_clock: Optional[float] = None,
                  run_time_cpu: Optional[float] = None,
                  run_time_cpu_inc_children: Optional[float] = None,
                  metadata: Optional[Dict[str, MetadataItem]] = None,
                  output_files: Optional[List[int]] = None):
        if attempt_id is not None:
            self.attempt_id = attempt_id
        if task_id is not None:
            self.task_id = task_id
        if start_time is not None:
            self.start_time = start_time
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
            self.output_files.union(output_files)

    def as_dict(self):
        """
        Turn a class instance into a Python dictionary, allowing it to be transmitted in JSON format.
        :return:
            Dict
        """
        return {"attempt_id": self.attempt_id,
                "task_id": self.task_id,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "all_products_passed_qc": self.all_products_passed_qc,
                "error_fail": self.error_fail,
                "error_text": self.error_text,
                "run_time_wall_clock": self.run_time_wall_clock,
                "run_time_cpu": self.run_time_cpu,
                "run_time_cpu_inc_children": self.run_time_cpu_inc_children,
                "metadata": [item.as_dict() for item in self.metadata.values()],
                "output_files": list(self.output_files)
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
        output = cls(attempt_id=d['attempt_id'],
                     task_id=d['task_id'],
                     start_time=d['start_time'],
                     end_time=d['end_time'],
                     all_products_passed_qc=d['all_products_passed_qc'],
                     error_fail=d['error_fail'],
                     error_text=d['error_text'],
                     run_time_wall_clock=d['run_time_wall_clock'],
                     run_time_cpu=d['run_time_cpu'],
                     run_time_cpu_inc_children=d['run_time_cpu_inc_children'],
                     output_files=set(d['output_files'])
                     )

        # Populate metadata
        for item in d['metadata']:
            item_object = MetadataItem.from_dict(item)
            output.configure(metadata={item_object.keyword: item_object})

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
        self.input_files: List[int] = []
        self.execution_attempts: Dict[int, TaskExecutionAttempt] = {}
        self.metadata: Dict[str, MetadataItem] = {}

        # Configure task
        self.configure(**kwargs)

    def configure(self, task_id: Optional[int] = None, parent_id: Optional[int] = None,
                  created_time: Optional[float] = None,
                  task_type: Optional[str] = None, job_name: Optional[str] = None,
                  working_directory: Optional[str] = None, input_files: Optional[List[int]] = None,
                  execution_attempts: List[TaskExecutionAttempt] = None,
                  metadata: Dict[str, MetadataItem] = None):
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
            # Replace existing list of input files with new list
            self.input_files = input_files
        if execution_attempts is not None:
            # Merge new execution attempts with existing list
            for item in execution_attempts:
                self.execution_attempts[item.attempt_id] = item
        if metadata is not None:
            # Merge new metadata with existing metadata
            for item in metadata.values():
                self.metadata[item.keyword] = item

    def as_dict(self):
        """
        Turn a class instance into a Python dictionary, allowing it to be transmitted in JSON format.
        :return:
            Dict
        """
        return {"task_id": self.task_id,
                "parent_id": self.parent_id,
                "created_time": self.created_time,
                "task_type": self.task_type,
                "job_name": self.job_name,
                "working_directory": self.working_directory,
                "input_files": self.input_files,
                "execution_attempts": [item.as_dict() for item in self.execution_attempts.values()],
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
        output = cls(task_id=d['task_id'],
                     parent_id=d['parent_id'],
                     created_time=d['created_time'],
                     task_type=d['task_type'],
                     job_name=d['job_name'],
                     working_directory=d['working_directory'],
                     input_files=d['input_files']
                     )

        # Populate execution attempts
        for item in d['execution_attempts']:
            output.configure(execution_attempts=[TaskExecutionAttempt.from_dict(item)])

        # Populate metadata
        for item in d['metadata']:
            item_object = MetadataItem.from_dict(item)
            output.configure(metadata={item_object.keyword: item_object})

        # Return output
        return output
