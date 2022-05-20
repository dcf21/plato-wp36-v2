#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# launch_service_mode.py

"""
Start working on tasks in service mode.
"""

import argparse
import logging
import os
import time

from plato_wp36 import container_name, logging_database, settings, task_database, task_queues

EasLoggingHandlerInstance = logging_database.EasLoggingHandler()


def enter_service_mode():
    """
    Start working on tasks in an infinite loop in service mode, listening to the message bus to receive the integer
    IDs of the tasks we should work on.

    :return:
        None
    """

    # Read list of task types from the database
    with task_database.TaskDatabaseConnection() as task_db:
        tasks = task_db.task_list_from_db()

    # Read list of task types that we are capable of performing
    container_name_string = container_name.get_container_name()
    container_capabilities = tasks.tasks_for_container(container_name=container_name_string)

    # Fetch EAS pipeline settings
    s = settings.Settings()

    # Enter an infinite processing loop
    while True:
        # Query each queue in turn
        for queue_name in container_capabilities:
            # Fetch messages from queue, one by one, until no more messages are found
            while True:
                # We are not currently running any task
                EasLoggingHandlerInstance.set_task_attempt_id()

                # Fetch a message from the message queue
                with task_queues.TaskQueueConnector().interface() as message_bus:
                    attempt_id = message_bus.queue_fetch_and_acknowledge(queue_name=queue_name)

                # Did we get a message?
                if attempt_id is None:
                    # Message queue was empty
                    break

                # Read execution attempt details from the database
                with task_database.TaskDatabaseConnection() as task_db:
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
