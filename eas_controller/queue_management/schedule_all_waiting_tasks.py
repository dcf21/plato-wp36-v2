#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# schedule_all_waiting_tasks.py

"""
Schedule all tasks in the database which have not yet been queued
"""

import argparse
import logging
import os
import time

from plato_wp36 import settings, task_database, task_queues


def schedule_jobs():
    """
    Schedule all tasks in the database which have not yet been queued.

    :return:
        None
    """

    # Read list of task types from the database
    task_db = task_database.TaskDatabaseConnection()

    # Open connection to the message queue
    message_bus = task_queues.TaskQueue()

    # Fetch list of all the tasks to schedule
    task_db.conn.execute("""
SELECT t.taskId, ett.taskName
FROM eas_task t
INNER JOIN eas_task_types ett on t.taskTypeId = ett.taskTypeId
WHERE NOT EXISTS (SELECT 1 FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId)
ORDER BY t.taskId;
""")
    tasks = task_db.conn.fetchall()

    # Schedule each job in turn
    for item in tasks:
        queue_name = item['taskName']
        task_id = item['taskId']
        logging.info("Scheduling {:6d} - {:s}".format(task_id, queue_name))
        attempt_id = task_db.execution_attempt_register(task_id=task_id)
        message_bus.queue_publish(queue_name=queue_name, message=attempt_id)

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

    # Reschedule tasks
    while True:
        schedule_jobs()
        time.sleep(5)
