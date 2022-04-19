#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# launch_service_mode.py

"""
Start working on tasks in service mode.
"""

import argparse
import json
import logging
import os
import time

from plato_wp36 import container_name, logging_database, settings, task_database, task_queues

EasLoggingHandlerInstance = logging_database.EasLoggingHandler()


def enter_service_mode():
    """
    Start working on tasks in service mode.

    :return:
        None
    """

    # Read list of task types from the database
    task_db = task_database.TaskDatabaseConnection()
    tasks = task_db.task_list_from_db()

    # Close database
    task_db.close_db()
    del task_db

    # Read list of task types that we are capable of performing
    container_name_string = container_name.get_container_name()
    container_capabilities = tasks.tasks_for_container(container_name=container_name_string)

    # Fetch testbench settings
    s = settings.Settings()

    # Open connection to the message queue
    message_bus = task_queues.TaskQueue()

    # Enter an infinite processing loop
    while True:
        # Query each queue in turn
        for queue_name in container_capabilities:
            # Fetch messages from queue, one by one, until no more messages are found
            while True:
                # We are not currently running any task
                EasLoggingHandlerInstance.set_task_attempt_id()

                # If we previously closed our connection to the message bus, reopen it now
                if message_bus is None:
                    # Reopen new connection to the message queue
                    message_bus = task_queues.TaskQueue()

                # Fetch a message from the message bux
                method_frame, header_frame, body = message_bus.queue_fetch(queue_name=queue_name)

                # Did we get a message?
                if method_frame is None or method_frame.NAME == 'Basic.GetEmpty':
                    # Message queue was empty
                    break
                else:
                    # Received a message. Close connection to the message queue, to prevent it timing out
                    message_bus.message_ack(method_frame=method_frame)
                    message_bus.close()
                    message_bus = None

                    # Extract task execution attempt id
                    attempt_id = int(json.loads(body))

                    # Read execution attempt details from the database
                    task_db = task_database.TaskDatabaseConnection()
                    attempt_info = task_db.execution_attempt_lookup(attempt_id=attempt_id)

                    # Check that execution attempt exists in the database
                    if attempt_info is None:
                        logging.warning("Could not find execution attempt <{}> in database".format(attempt_id))
                        continue

                    # Set log messages to reference this execution attempt
                    EasLoggingHandlerInstance.set_task_attempt_id(attempt_id=attempt_id)

                    # Read task type from the database
                    task_info = task_db.task_lookup(task_id=attempt_info.task_id)
                    task_name = task_info.task_type

                    # Close database
                    task_db.close_db()
                    del task_db

                    # Announce that we're running a task
                    logging.info("Starting task execution attempt <{} - {}>".format(attempt_id, task_name))

                    # The filename where we expect to find the Python script that implements this task
                    task_implementation = os.path.abspath(os.path.join(
                        s.settings['pythonPath'], 'task_implementations', 'task_{}.py'.format(task_name)
                    ))

                    # Check that task implementation exists
                    if not os.path.exists(path=task_implementation):
                        logging.error("Could not find task implementation <{}>.".format(task_implementation))
                    if not os.access(task_implementation, os.X_OK):
                        logging.error("Task implementation <{}> is not an executable.".format(task_implementation))

                    # Launch task handler
                    os.system("{} --job-id {}".format(task_implementation, attempt_id))

                    # Announce that we're moving onto post-execution QC
                    logging.info("Starting QC on task execution attempt <{} - {}>".format(attempt_id, task_name))

                    # The filename where we expect to find the Python script that implements QC for this task
                    task_qc_implementation = os.path.abspath(os.path.join(
                        s.settings['pythonPath'], 'task_qc_implementations', 'task_{}.py'.format(task_name)
                    ))

                    # Check that task implementation exists
                    if not os.path.exists(path=task_qc_implementation):
                        logging.error("Could not find task QC implementation <{}>.".format(task_implementation))
                    if not os.access(task_qc_implementation, os.X_OK):
                        logging.error("Task QC implementation <{}> is not an executable.".format(task_implementation))

                    # Launch task QC handler
                    os.system("{} --job-id {}".format(task_qc_implementation, attempt_id))

                    # Announce that we've finished a task
                    logging.info("Finished task execution attempt <{} - {}>".format(attempt_id, task_name))

        # To avoid clobbering the database, have a quick snooze between polling to see if we have work to do
        time.sleep(10)

    # Close connection
    if message_bus is not None:
        message_bus.close()
        message_bus = None


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        handlers=[EasLoggingHandlerInstance, logging.StreamHandler()]
                        )
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # List for jobs from the message queues
    enter_service_mode()
