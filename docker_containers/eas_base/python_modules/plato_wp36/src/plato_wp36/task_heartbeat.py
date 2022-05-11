# -*- coding: utf-8 -*-
# task_heartbeat.py

"""
A class which can be used to wrap segments of code, and sends regular heartbeat updates to the task database to indicate
that a child process is still alive and working on the task. To use, wrap your code as follows:

with TaskHeartbeat( <settings> ):
    <code_segment>

"""

import os
import subprocess

from typing import Optional

from .settings import Settings


class TaskHeartbeat:
    """
    A class which can be used to wrap segments of code, and sends regular heartbeat updates to the task database to
    indicate that a child process is still alive and working on the task.
    """

    def __init__(self, task_attempt_id: Optional[int] = None, heartbeat_cadence: float = 60):
        """
        Create a new heartbeat process.

        :param task_attempt_id:
            The integer ID of the task attempt that is being timed, in the <eas_scheduling_attempt> table.
        :type task_attempt_id:
            int
        :param heartbeat_cadence:
            The period, in seconds, between the heartbeat updates.
        :type heartbeat_cadence:
            float
        """

        # Store the state of this heartbeat process
        self.task_attempt_id = task_attempt_id
        self.heartbeat_cadence = heartbeat_cadence

        # Fetch EAS settings
        s = Settings()

        # Path to the subprocess script
        self.heartbeat_script = os.path.join(
            s.settings['pythonPath'], 'python_components', 'heartbeat_process.py'
        )

    def __enter__(self):
        """
        Start a heartbeat process
        """

        # Create a heartbeat subprocess
        self.process = subprocess.Popen(args=[self.heartbeat_script,
                                              "--pid", str(os.getpid()),
                                              "--attempt-id", str(self.task_attempt_id),
                                              "--cadence", str(self.heartbeat_cadence)
                                              ])

        # Finished
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Stop the heartbeat process

        :param exc_type:
            Exception type
        :param exc_val:
            Exception value
        :param exc_tb:
            Exception traceback
        :return:
        """

        # Terminate the heartbeat process
        self.process.terminate()
