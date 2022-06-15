#!../../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# launch_standalone.py

"""
Start working on tasks in a standalone container environment
"""

import argparse
import configparser
import json
import logging
import sys

from plato_wp36 import connect_db, task_database, task_queues, task_types

from launch_service_mode import enter_service_mode


def run_standalone_task(config_file: str):
    """
    Start working on a single task within a stand-alone Docker container

    :param config_file:
        The filename of a configuration file listing the inputs and outputs for the task we are to run.
    :return:
        None
    """

    # Database settings for use in stand-alone mode
    db_engine = "sqlite3"
    db_database = "plato"
    db_user = "root"
    db_passwd = "plato"
    db_host = "localhost"
    db_port = 3306

    queue_implementation = "sql"
    mq_user = "guest"
    mq_passwd = "guest"
    mq_host = "localhost"
    mq_port = 5672

    # Write configuration files, so we know how to connect to the task database and message queue
    with connect_db.DatabaseConnector(db_engine=db_engine, db_database=db_database,
                                      db_user=db_user, db_passwd=db_passwd,
                                      db_host=db_host, db_port=db_port).interface(connect=False) as db:
        db.make_sql_login_config()
        db.create_database(initialise_schema=True)

    # Read list of known task types
    tasks = task_types.TaskTypeList.read_from_xml()

    # Write list of task types to the database
    with task_database.TaskDatabaseConnection() as task_db:
        task_db.task_type_list_to_db(task_list=tasks)

    # Create message queue connection config file
    task_queues.TaskQueueConnector.make_task_queue_config(queue_implementation=queue_implementation,
                                                          mq_user=mq_user, mq_passwd=mq_passwd,
                                                          mq_host=mq_host, mq_port=mq_port)

    # Extract description of the task we are to run
    config_parser = configparser.ConfigParser()
    config_parser.read(filenames=config_file)

    # Create task description data structure
    task_type = config_parser['task'].get('task', 'null')
    working_directory = config_parser['task'].get('working_directory', 'null')
    job_name = config_parser['task'].get('job_name', 'null')
    task_name = config_parser['task'].get('task_name', 'null')

    task_decription = {
        'task': task_type,
        'working_directory': working_directory,
        'job_name': job_name,
        'task_name': task_name
    }

    task_metadata = {
        'task_description': json.dumps(task_decription)
    }

    # Create task entry in database
    with task_database.TaskDatabaseConnection() as task_db:
        new_task_id = task_db.task_register(task_type=task_type,
                                            working_directory=working_directory,
                                            job_name=job_name,
                                            task_name=task_name,
                                            metadata=task_metadata
                                            )

    # Add the task to the job queue
    with task_queues.TaskScheduler() as scheduler:
        scheduler.schedule_a_task(task_id=new_task_id)

    # Actually run the task
    enter_service_mode(db_engine=db_engine, db_user=db_user, db_passwd=db_passwd, db_host=db_host,
                       db_port=db_port, db_name=db_database,
                       queue_implementation=queue_implementation,
                       mq_user=mq_user, mq_passwd=mq_passwd, mq_host=mq_host, mq_port=mq_port,
                       infinite_loop=False)


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=str, dest='config',
                        help='Configuration file specifying task inputs and outputs')
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        stream=sys.stdout
                        )
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # Run a single task in stand-alone mode
    run_standalone_task(config_file=args.config)
