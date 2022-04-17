#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# empty_queue.py

"""
Flush all messages out of the RabbitMQ message queues
"""

import logging
import os

import argparse

from plato_wp36 import settings, task_database, task_queues


def flush_queues():
    """
    Flush all messages out of the RabbitMQ message queues
    :return:
        None
    """

    # Read list of task types from the database
    task_db = task_database.TaskDatabaseConnection()
    tasks = task_db.task_list_from_db()

    # Open connection to the message queue
    message_bus = task_queues.TaskQueue()

    # Query each queue in turn
    for queue_name in tasks.task_names():
        # Fetch messages from queue, one by one, until no more messages are found
        while True:
            method_frame, header_frame, body = message_bus.queue_fetch(queue_name=queue_name)

            if method_frame is None or method_frame.NAME == 'Basic.GetEmpty':
                # Message queue was empty
                break
            else:
                # Received a message
                message_bus.message_ack(method_frame=method_frame)

    # Close connection
    message_bus.close()

    # Commit database
    task_db.commit()
    task_db.close_db()


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()

    # Fetch testbench settings
    settings = settings.Settings()

    # Set up logging
    log_file_path = os.path.join(settings.settings['dataPath'], 'plato_wp36.log')
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        handlers=[
                            logging.FileHandler(log_file_path),
                            logging.StreamHandler()
                        ])
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # Flush the contents of the message queues
    flush_queues()
