# -*- coding: utf-8 -*-
# logging_database.py

"""
A custom log handler class, which sends all logs messages to the EAS status database.
"""

import logging
import time

from typing import Optional

from .connect_db import DatabaseConnector
from .settings import Settings


class EasLoggingHandler(logging.StreamHandler):
    """
    A custom log handler, which sends all logs messages to the EAS status database.
    """

    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.current_task_attempt_id = None

        # Fetch EAS settings
        self.settings = Settings()

    def set_task_attempt_id(self, attempt_id: Optional[int] = None):
        """
        Set the ID of the execution attempt we are currently running, so that this is recorded in any log messages.
        :param attempt_id:
            The ID of the execution attempt.
        :return:
            None
        """
        self.current_task_attempt_id = attempt_id

    def emit(self, record):
        """
        Record a logging message.

        :param record:
            The logging message to record to the database
        :return:
            None
        """
        # Open connection to the database
        with DatabaseConnector().connect_db() as db_handle:
            # Truncate log message if necessary
            log_message = str(record.msg)
            max_message_length = int(self.settings.installation_info['max_log_message_length'])
            if len(log_message) > max_message_length:
                log_message = "{}...".format(log_message[:max_message_length - 5])

            # File logging message
            db_handle.parameterised_query("""
INSERT INTO eas_log_messages (generatedByTaskExecution, timestamp, severity, message)
VALUES (%s, %s, %s, %s);
""", (self.current_task_attempt_id, time.time(), record.levelno, log_message))
