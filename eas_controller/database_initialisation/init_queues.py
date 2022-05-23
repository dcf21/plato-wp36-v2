#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# init_queues.py

"""
Create a set of empty queues in the message bus, and configure the credentials we will use to connect in the future.
"""

import argparse
import logging
import os

from plato_wp36 import settings, task_database, task_queues


def init_queues(queue_implementation: str, mq_user: str, mq_passwd: str, mq_host: str, mq_port: int):
    """
    Create message bus queues, and configure the credentials we will use to connect in the future.

    :param queue_implementation:
        The name of the task queue implementation we are using. Either <amqp> or <sql>.
    :param mq_user:
        The username to use when connecting to an AMQP-based task queue.
    :param mq_passwd:
        The password to use when connecting to an AMQP-based task queue.
    :param mq_host:
        The host to use when connecting to an AMQP-based task queue.
    :param mq_port:
        The port number to use when connecting to an AMQP-based task queue.
    :return:
        None
    """

    # Create mysql login config file
    task_queues.TaskQueueConnector.make_task_queue_config(queue_implementation=queue_implementation,
                                                          mq_user=mq_user, mq_passwd=mq_passwd,
                                                          mq_host=mq_host, mq_port=mq_port)

    # Read list of task types from the database
    with task_database.TaskDatabaseConnection() as task_db:
        tasks = task_db.task_type_list_from_db()

        # Open connection to the message queue
        with task_queues.TaskQueueConnector().interface() as message_bus:
            # Declare each queue in turn
            for queue_name in tasks.task_type_names():
                message_bus.queue_declare(queue_name=queue_name)


# Do it right away if we're run as a script
if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--queue_implementation', default="amqp", type=str, dest='queue_implementation',
                        choices=("amqp", "sql"),
                        help='The name of the task queue implementation we are using. Either <amqp> or <sql>.')
    parser.add_argument('--mq_user', default="guest", type=str, dest='mq_user', help='AMQP username')
    parser.add_argument('--mq_passwd', default="guest", type=str, dest='mq_passwd', help='AMQP password')
    parser.add_argument('--mq_host', default="localhost", type=str, dest='mq_host', help='AMQP host')
    parser.add_argument('--mq_port', default=5672, type=int, dest='mq_port', help='AMQP port')
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

    # Initialise schema
    init_queues(queue_implementation=args.queue_implementation,
                mq_user=args.mq_user, mq_passwd=args.mq_passwd,
                mq_host=args.mq_host, mq_port=args.mq_port)
