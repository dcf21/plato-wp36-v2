#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# launch_service_mode.py

"""
Start working on tasks in service mode.
"""

import argparse
import glob
import logging
import os
import re
import time

from plato_wp36 import connect_db, logging_database, settings, task_database, task_execution, task_queues

EasLoggingHandlerInstance = logging_database.EasLoggingHandler()


def error_fail(attempt_id: int, error_message: str):
    """
    Report that a task execution attempt failed.

    :param attempt_id:
        The integer ID of the task execution attempt which failed
    :param error_message:
        The error message associated with this task failure
    """

    # Log an error message
    logging.error(error_message)

    # Open a connection to the EasControl task database
    with task_database.TaskDatabaseConnection() as task_db:
        # Record the failure of this task
        task_db.execution_attempt_update(attempt_id=attempt_id, is_queued=False, is_running=False, is_finished=True,
                                         error_fail=True, error_text=error_message)


def enter_service_mode(db_engine: str, db_user: str, db_passwd: str, db_host: str, db_port: int, db_name: str,
                       queue_implementation: str, mq_user: str, mq_passwd: str, mq_host: str, mq_port: int,
                       infinite_loop: bool = True):
    """
    Start working on tasks in an infinite loop in service mode, listening to the message bus to receive the integer
    IDs of the tasks we should work on.

    :param db_engine:
        The name of the SQL database engine we are using. Either <mysql> or <sqlite3>.
    :param db_name:
        The name of the database we should connect to
    :param db_user:
        The name of the database user (not used by sqlite3)
    :param db_passwd:
        The password for the database user (not used by sqlite3)
    :param db_host:
        The host on which the database server is running (not used by sqlite3)
    :param db_port:
        The port on which the database server is running (not used by sqlite3)
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
    :param infinite_loop:
        If true then we loop forever, waiting for new tasks to enter the job queue. If false, then we exit when
        job queue is empty.

    :return:
        None
    """

    # Write configuration files, so we know how to connect to the task database and message queue
    with connect_db.DatabaseConnector(db_engine=db_engine, db_database=db_name,
                                      db_user=db_user, db_passwd=db_passwd,
                                      db_host=db_host, db_port=db_port).interface(connect=False) as db:
        db.make_sql_login_config()

    # Create message queue connection config file
    task_queues.TaskQueueConnector.make_task_queue_config(queue_implementation=queue_implementation,
                                                          mq_user=mq_user, mq_passwd=mq_passwd,
                                                          mq_host=mq_host, mq_port=mq_port)

    # Read list of task types that we are capable of performing, by looking at what Python scripts are
    # available in the <task_implementations> directory
    available_tasks = glob.glob(os.path.join(os.path.dirname(__file__), "../task_implementations/task_*.py"))
    container_capabilities = []

    # Extract the name of each available task in turn
    for item in available_tasks:
        task_type_name = re.search(r"task_([^/]*).py", item).group(1)
        container_capabilities.append(task_type_name)

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
                    attempt_info = task_db.execution_attempt_lookup(attempt_id=attempt_id, embed_task_object=False)

                    # Check that execution attempt exists in the database
                    if attempt_info is None:
                        logging.warning("Could not find execution attempt <{}> in database".format(attempt_id))
                        continue

                    # Set log messages to reference this execution attempt
                    EasLoggingHandlerInstance.set_task_attempt_id(attempt_id=attempt_id)

                    # Read task type from the database
                    task_info = task_db.task_lookup(task_id=attempt_info.task_id)
                    task_type_name = task_info.task_type

                # Announce that we're running a task
                logging.info("Starting task execution attempt <{} - {}>".format(attempt_id, task_type_name))

                # The filename where we expect to find the Python script that implements this task
                task_implementation = os.path.abspath(os.path.join(
                    s.settings['pythonPath'], 'task_implementations', 'task_{}.py'.format(task_type_name)
                ))

                # Check that task implementation exists
                if not os.path.exists(path=task_implementation):
                    error_fail(
                        attempt_id=attempt_id,
                        error_message="Could not find task implementation <{}>.".format(task_implementation)
                    )
                    continue
                if not os.access(task_implementation, os.X_OK):
                    error_fail(
                        attempt_id=attempt_id,
                        error_message="Task implementation <{}> is not an executable.".format(task_implementation)
                    )
                    continue

                # Launch task handler
                task_executed_ok = task_execution.call_subprocess_and_log_output(
                    arguments=(task_implementation, "--job-id", attempt_id)
                )

                if not task_executed_ok:
                    error_fail(attempt_id=attempt_id, error_message="Task implementation returned non-zero status")
                    continue

                # Announce that we're moving onto post-execution QC
                logging.info("Starting QC on task execution attempt <{} - {}>".format(attempt_id, task_type_name))

                # The filename where we expect to find the Python script that implements QC for this task
                task_qc_implementation = os.path.abspath(os.path.join(
                    s.settings['pythonPath'], 'task_qc_implementations', 'task_{}.py'.format(task_type_name)
                ))

                # Check that task implementation exists
                if not os.path.exists(path=task_qc_implementation):
                    logging.error("Could not find task QC implementation <{}>.".format(task_implementation))
                    error_fail(
                        attempt_id=attempt_id,
                        error_message="Could not find task QC implementation <{}>.".format(task_implementation)
                    )
                    continue
                if not os.access(task_qc_implementation, os.X_OK):
                    error_fail(
                        attempt_id=attempt_id,
                        error_message="Task QC implementation <{}> is not an executable.".format(task_implementation)
                    )
                    continue

                # Launch task QC handler
                task_execution.call_subprocess_and_log_output(
                    arguments=(task_qc_implementation, "--job-id", attempt_id)
                )

                # Announce that we've finished a task
                logging.info("Finished task execution attempt <{} - {}>".format(attempt_id, task_type_name))

        if not infinite_loop:
            # If we're not running in an infinite loop, then exit after we've emptied the job queues
            break
        else:
            # To avoid clobbering the database, have a quick snooze between polling to see if we have work to do
            time.sleep(2)


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db_engine', default="mysql", type=str, dest='db_engine', help='Database engine')
    parser.add_argument('--db_user', default="root", type=str, dest='db_user', help='Database user')
    parser.add_argument('--db_passwd', default="plato", type=str, dest='db_passwd', help='Database password')
    parser.add_argument('--db_host', default="localhost", type=str, dest='db_host', help='Database host')
    parser.add_argument('--db_port', default=30036, type=int, dest='db_port', help='Database port')
    parser.add_argument('--db_name', default="plato", type=str, dest='db_name', help='Database name')
    parser.add_argument('--queue_implementation', default="amqp", type=str, dest='queue_implementation',
                        choices=("amqp", "sql"),
                        help='The name of the task queue implementation we are using. Either <amqp> or <sql>.')
    parser.add_argument('--mq_user', default="guest", type=str, dest='mq_user', help='AMQP username')
    parser.add_argument('--mq_passwd', default="guest", type=str, dest='mq_passwd', help='AMQP password')
    parser.add_argument('--mq_host', default="localhost", type=str, dest='mq_host', help='AMQP host')
    parser.add_argument('--mq_port', default=5672, type=int, dest='mq_port', help='AMQP port')
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        handlers=[EasLoggingHandlerInstance, logging.StreamHandler()]
                        )
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # Listen for jobs from the message queues
    enter_service_mode(db_engine=args.db_engine,
                       db_user=args.db_user, db_passwd=args.db_passwd,
                       db_host=args.db_host, db_port=args.db_port,
                       db_name=args.db_name,
                       queue_implementation=args.queue_implementation,
                       mq_user=args.mq_user, mq_passwd=args.mq_passwd,
                       mq_host=args.mq_host, mq_port=args.mq_port
                       )
