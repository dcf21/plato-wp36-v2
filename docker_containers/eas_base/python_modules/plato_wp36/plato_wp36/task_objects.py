# -*- coding: utf-8 -*-
# task_objects.py

"""
Pythonic objects to represent pipeline task entries in the database
"""

from typing import Dict, List, Optional


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

        # Configure task
        self.configure(**kwargs)

    def configure(self, attempt_id: Optional[int] = None, task_id: Optional[int] = None,
                  start_time: Optional[float] = None, end_time: Optional[float] = None,
                  all_products_passed_qc: Optional[bool] = None,
                  error_fail: Optional[bool] = None, error_text: Optional[str] = None,
                  run_time_wall_clock: Optional[float] = None,
                  run_time_cpu: Optional[float] = None,
                  run_time_cpu_inc_children: Optional[float] = None):
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
                "run_time_cpu_inc_children": self.run_time_cpu_inc_children
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
        return cls(attempt_id=d['attempt_id'],
                   task_id=d['task_id'],
                   start_time=d['start_time'],
                   end_time=d['end_time'],
                   all_products_passed_qc=d['all_products_passed_qc'],
                   error_fail=d['error_fail'],
                   error_text=d['error_text'],
                   run_time_wall_clock=d['run_time_wall_clock'],
                   run_time_cpu=d['run_time_cpu'],
                   run_time_cpu_inc_children=d['run_time_cpu_inc_children']
                   )


class Task:
    """
    Python class to represent a task in the <eas_task> database table.
    """

    def __init__(self, **kwargs):
        # Initialise null task
        self.task_id: Optional[int] = None
        self.parent_id: Optional[int] = None
        self.task_type: Optional[str] = None
        self.execution_attempts: List[TaskExecutionAttempt] = []

        # Configure task
        self.configure(**kwargs)

    def configure(self, task_id: Optional[int] = None, parent_id: Optional[int] = None,
                  task_type: Optional[str] = None, execution_attempts: List[TaskExecutionAttempt] = None):
        if task_id is not None:
            self.task_id = task_id
        if parent_id is not None:
            self.parent_id = parent_id
        if task_type is not None:
            self.task_type = task_type
        if execution_attempts is not None:
            self.execution_attempts = execution_attempts

    def add_execution_attempt(self, execution_attempt: TaskExecutionAttempt):
        self.execution_attempts.append(execution_attempt)

    def as_dict(self):
        """
        Turn a class instance into a Python dictionary, allowing it to be transmitted in JSON format.
        :return:
            Dict
        """
        return {"task_id": self.task_id,
                "parent_id": self.parent_id,
                "task_type": self.task_type,
                "execution_attempts": [item.as_dict() for item in self.execution_attempts]
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
        return cls(task_id=d['task_id'],
                   parent_id=d['parent_id'],
                   task_type=d['task_type'],
                   execution_attempts=[TaskExecutionAttempt.from_dict(item) for item in d['execution_attempts']]
                   )
