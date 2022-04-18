#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# display_message_queue.py

"""
Display the contents of the RabbitMQ message queues.
"""

import json
import logging
import os

import argparse

from plato_wp36 import settings, task_database, task_queues


def print_queues():
    """
    Print the status of all the job queues in RabbitMQ in turn.

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
        message_count = message_bus.queue_length(queue_name=queue_name)
        logging.info("{:s} ({:d} messages waiting)".format(queue_name, message_count))

        message_list = []

        # Fetch messages from queue, one by one, until no more messages are found
        while True:
            method_frame, header_frame, body = message_bus.queue_fetch(queue_name=queue_name)

            if method_frame is None or method_frame.NAME == 'Basic.GetEmpty':
                # Message queue was empty
                break
            else:
                # Received a message
                message_list.append(json.loads(body))

        # Display list of all the messages
        if len(message_list) > 0:
            logging.info(str(message_list))

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

    # Display the contents of the message queues
    print_queues()
