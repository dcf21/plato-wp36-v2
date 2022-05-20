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
    with task_database.TaskDatabaseConnection() as task_db:
        tasks = task_db.task_list_from_db()

    # Open connection to the message queue
    with task_queues.TaskQueueConnector().interface() as message_bus:
        # Query each queue in turn
        for queue_name in tasks.task_names():
            message_count = message_bus.queue_length(queue_name=queue_name)
            logging.info("{:s} ({:d} messages waiting)".format(queue_name, message_count))

            # Fetch messages from queue, one by one, until no more messages are found
            message_list = message_bus.queue_fetch_list(queue_name=queue_name)

            # Display list of all the messages
            if len(message_list) > 0:
                logging.info(str(message_list))


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    args = parser.parse_args()

    # Fetch EAS pipeline settings
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
