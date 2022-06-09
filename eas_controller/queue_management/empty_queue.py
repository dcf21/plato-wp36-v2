#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# empty_queue.py

"""
Flush all messages out of the RabbitMQ message queues.
"""

import argparse
import logging
import os

from plato_wp36 import settings, task_database, task_queues


def flush_queues():
    """
    Flush all messages out of the RabbitMQ message queues.

    :return:
        None
    """

    # Read list of task types from the database
    with task_database.TaskDatabaseConnection() as task_db:
        tasks = task_db.task_type_list_from_db()

    # Open connection to the message queue
    with task_queues.TaskQueueConnector().interface() as message_bus:
        # Query each queue in turn
        for queue_name in tasks.task_type_names():
            # Count how many queue items we have removed
            counter = 0
            # Fetch messages from queue, one by one, until no more messages are found
            while True:
                if counter % 1000 == 0:
                    queue_count = message_bus.queue_length(queue_name=queue_name)
                    logging.info("Removing items from queue <{}> -- {:6d} items".format(queue_name, queue_count))

                # Remove an item from the queue
                task_id = message_bus.queue_fetch_and_acknowledge(queue_name=queue_name, set_running=False)

                counter += 1

                if task_id is None:
                    # Message queue was empty
                    break


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

    # Flush the contents of the message queues
    flush_queues()
