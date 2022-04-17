#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# init_queues.py

"""
Create a set of empty queues in the message bus, and configure the credentials we will use to connect in the future.
"""

import argparse
import logging
import os

from plato_wp36 import connect_db, settings, task_database, task_queues


def init_queues(mq_user: str, mq_passwd: str, mq_host: str, mq_port: int):
    """
    Create message bus queues, and configure the credentials we will use to connect in the future.

    :return:
        None
    """

    # Instantiate database connection class
    db = connect_db.DatabaseConnector()

    # Create mysql login config file
    db.make_amqp_login_config(mq_user=mq_user, mq_passwd=mq_passwd,
                              mq_host=mq_host, mq_port=mq_port)

    # Read list of task types from the database
    task_db = task_database.TaskDatabaseConnection()
    tasks = task_db.task_list_from_db()

    # Open connection to the message queue
    message_bus = task_queues.TaskQueue()

    # Declare each queue in turn
    for queue_name in tasks.task_names():
        message_bus.queue_declare(queue_name=queue_name)

    # Close connection
    message_bus.close()

    # Commit database
    task_db.commit()
    task_db.close_db()


# Do it right away if we're run as a script
if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mq_user', default="guest", type=str, dest='mq_user', help='AMQP user')
    parser.add_argument('--mq_passwd', default="guest", type=str, dest='mq_passwd', help='AMQP password')
    parser.add_argument('--mq_host', default="localhost", type=str, dest='mq_host', help='AMQP host')
    parser.add_argument('--mq_port', default=5672, type=int, dest='mq_port', help='AMQP port')
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

    # Initialise schema
    init_queues(mq_user=args.mq_user, mq_passwd=args.mq_passwd,
                mq_host=args.mq_host, mq_port=args.mq_port)
