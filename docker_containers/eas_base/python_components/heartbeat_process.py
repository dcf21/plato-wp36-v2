#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# heartbeat_process.py

"""
Launch a heartbeat process which sends regular heartbeat updates to the task database to indicate that a task attempt
is still alive and running.
"""

import argparse
import logging
import psutil
import sys
import time
import traceback

from plato_wp36 import connect_db, logging_database

EasLoggingHandlerInstance = logging_database.EasLoggingHandler()


def start_heartbeat(parent_pid: int, task_attempt_id: int, heartbeat_cadence: int = 60):
    """
    Start sending heartbeat updates to the database.

    :param parent_pid:
        The PID of the process working on the task. If this process terminates, we stop sending heartbeats.
    :type parent_pid:
        int
    :param task_attempt_id:
        The integer uid of the task attempt that we are sending heartbeats for.
    :type task_attempt_id:
        int
    :param heartbeat_cadence:
        The interval, in seconds, between heartbeat updates.
    :type heartbeat_cadence:
        int
    :return:
        None
    """

    # Set logging task execution attempt id
    EasLoggingHandlerInstance.set_task_attempt_id(attempt_id=task_attempt_id)

    # Log start of heartbeat
    logging.info("Starting heartbeat for <{}>".format(task_attempt_id))

    # Enter an infinite processing loop
    while True:
        # Catch all exceptions, and record them in the logging database
        try:
            # Check that child process is still alive
            if not psutil.pid_exists(parent_pid):
                logging.info("Ending heartbeat for <{:d}> (process {:d} has gone away)".
                             format(task_attempt_id, parent_pid))
                sys.exit(0)

            # Open connection to the database
            with connect_db.DatabaseConnector().connect_db() as db_handle:
                # Log heartbeat
                logging.info("Heartbeat for <{}>".format(task_attempt_id))

                # Send heartbeat to the database
                db_handle.parameterised_query("""
UPDATE eas_scheduling_attempt
SET latestHeartbeat=%s
WHERE schedulingAttemptId=%s;
""", (time.time(), task_attempt_id))

        except Exception:
            error_message = traceback.format_exc()
            logging.error(error_message)

        # Wait until next heartbeat
        time.sleep(heartbeat_cadence)


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pid', required=True, type=int, dest='parent_pid',
                        help='The PID of the process running the task')
    parser.add_argument('--attempt-id', required=True, type=int, dest='task_attempt_id',
                        help='The integer ID of the task attempt to provide a heartbeat for')
    parser.add_argument('--cadence', default=60, type=float, dest='heartbeat_cadence',
                        help='The interval, in seconds, between the heartbeats')
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        handlers=[EasLoggingHandlerInstance, logging.StreamHandler()]
                        )
    logger = logging.getLogger(__name__)

    # List for jobs from the message queues
    start_heartbeat(parent_pid=args.parent_pid,
                    task_attempt_id=args.task_attempt_id,
                    heartbeat_cadence=args.heartbeat_cadence)
