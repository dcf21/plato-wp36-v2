# -*- coding: utf-8 -*-
# task_timer.py

"""
A class which can be used to wrap segments of code, and time how long they take to run, in both wall-clock time and also
CPU time. To use, wrap your code as follows:

with TaskTimer( <settings> ):
    <code_segment>

"""

import platform
import resource
import time

from typing import Optional

from .connect_db import DatabaseConnector


class TaskTimer:
    """
    A class which can be used to wrap segments of code, and time how long they take to run, in both wall-clock time
    and also CPU time.
    """

    def __init__(self, task_attempt_id: Optional[int] = None):
        """
        Create a new timer.

        :param task_attempt_id:
            The integer ID of the task attempt that is being timed, in the <eas_scheduling_attempt> table.
        :type task_attempt_id:
            int
        """

        # Store the state of this timer
        self.task_attempt_id = task_attempt_id

    @staticmethod
    def measure_time():
        """
        Implementation of the function(s) we use to measure how long this process has been running.

        :return:
            A dictionary of time measurements
        """
        return {
            # Wall clock time
            'wall_clock': time.time(),

            # CPU core seconds
            'cpu': time.process_time(),

            # CPU core seconds as reported by <resource> package, including child processes
            'cpu_inc_children': resource.getrusage(resource.RUSAGE_SELF).ru_utime +
                                resource.getrusage(resource.RUSAGE_SELF).ru_stime +
                                resource.getrusage(resource.RUSAGE_CHILDREN).ru_utime +
                                resource.getrusage(resource.RUSAGE_CHILDREN).ru_stime
        }

    def __enter__(self):
        """
        Start timing a task
        """

        # Record the start time of the task
        self.start_time = self.measure_time()

        # Open connection to the database
        db_connector = DatabaseConnector()
        db, conn = db_connector.connect_db()

        # File task execution time in the database
        conn.execute("""
UPDATE eas_scheduling_attempt
SET startTime=%s, latestHeartbeat=%s, hostname=%s
WHERE schedulingAttemptId=%s;
""", (self.start_time['wall_clock'], self.start_time['wall_clock'], platform.node(), self.task_attempt_id))

        # Commit changes to the database
        db.commit()
        db.close()

        # Finished
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop timing the task

        :param exc_type:
            Exception type
        :param exc_val:
            Exception value
        :param exc_tb:
            Exception traceback
        :return:
        """

        # Record the end time of the task
        self.end_time = self.measure_time()

        # Calculate run time
        run_times = {}
        for key in self.end_time:
            run_times[key] = self.end_time[key] - self.start_time[key]

        # Open connection to the database
        db_connector = DatabaseConnector()
        db, conn = db_connector.connect_db()

        # File task execution time in the database
        conn.execute("""
UPDATE eas_scheduling_attempt
SET endTime=%s, runTimeWallClock=%s, runTimeCpu=%s, runTimeCpuIncChildren=%s
WHERE schedulingAttemptId=%s;
""",
                     (time.time(),
                      run_times['wall_clock'], run_times['cpu'], run_times['cpu_inc_children'],
                      self.task_attempt_id))

        # Commit changes to the database
        db.commit()
        db.close()
