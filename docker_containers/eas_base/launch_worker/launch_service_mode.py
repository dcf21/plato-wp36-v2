#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# launch_service_mode.py

"""
Start working on tasks in service mode.
"""

import argparse
import json
import logging
import time
import traceback

from plato_wp36 import container_name, logging_database, task_database, task_queues, task_timer

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
    task_db.commit()
    task_db.close_db()
    del task_db

    # Read list of task types that we are capable of performing
    container_name_string = container_name.get_container_name()
    container_capabilities = tasks.tasks_for_container(container_name=container_name_string)

    # Open connection to the message queue
    message_bus = task_queues.TaskQueue()

    # Enter an infinite processing loop
    while True:
        time.sleep(5)

        # Query each queue in turn
        for queue_name in container_capabilities:
            # Fetch messages from queue, one by one, until no more messages are found
            while True:
                method_frame, header_frame, body = message_bus.queue_fetch(queue_name=queue_name)

                if method_frame is None or method_frame.NAME == 'Basic.GetEmpty':
                    # Message queue was empty
                    break
                else:
                    # Received a message. Close connection to the message queue, to prevent it timing out
                    message_bus.message_ack(method_frame=method_frame)
                    message_bus.close()

                    # Extract task execution attempt id
                    attempt_id = json.loads(body)
                    EasLoggingHandlerInstance.set_task_attempt_id(attempt_id=attempt_id)

                    # Start task timer
                    with task_timer.TaskTimer(task_attempt_id=attempt_id):
                        # Catch all exceptions, and record them in the logging database
                        try:
                            # Announce that we're running a task
                            logging.info("Starting task execution attempt <{}>".format(attempt_id))

                            # Launch task handler
                        except Exception:
                            error_message = traceback.format_exc()
                            logging.error(error_message)

                    # Finished task
                    EasLoggingHandlerInstance.set_task_attempt_id()

                    # Reopen new connection to the message queue
                    message_bus = task_queues.TaskQueue()

    # Close connection
    message_bus.close()


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
