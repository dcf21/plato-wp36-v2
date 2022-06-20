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
import os
import sys
import time

from plato_wp36 import connect_db, settings, task_database, task_queues, task_types

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

    # Fetch EAS pipeline settings
    s = settings.Settings()

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

    # Start creating task description data structure
    task_type = config_parser['task'].get('task', 'null')
    working_directory = config_parser['task'].get('working_directory', 'test_dir')
    job_name = config_parser['task'].get('job_name', 'test_job')
    task_name = config_parser['task'].get('task_name', 'untitled_test')

    task_description = {
        'task': task_type,
        'working_directory': working_directory,
        'job_name': job_name,
        'task_name': task_name
    }

    # Add custom settings for task
    for config_section in config_parser.keys():
        if config_section == 'task':
            target = task_description
        else:
            if config_section not in task_description:
                task_description[config_section] = {}
            target = task_description[config_section]
        for config_key in config_parser[config_section].keys():
            if config_key not in target:
                target[config_key] = config_parser[config_section][config_key]

    # Create a null parent task, which we associate with any input file products required by the task we are to run
    with task_database.TaskDatabaseConnection() as task_db:
        parent_task_id = task_db.task_register(task_type="null",
                                               working_directory=working_directory,
                                               job_name="parent",
                                               task_name="parent"
                                               )

        # Create an execution attempt for the parent task
        parent_attempt_id = task_db.execution_attempt_register(task_id=parent_task_id)

        # Import all input files
        if 'inputs' in config_parser:
            for semantic_type, input_filename in config_parser['inputs'].items():
                logging.info("Importing input <{}> -> <{}>".format(semantic_type, input_filename))

                input_full_path = os.path.join(s.settings['pythonPath'], input_filename)

                # Create file product entry for this input file
                name = os.path.split(input_filename)[1]
                product_id = task_db.file_product_register(generator_task=parent_task_id,
                                                           directory=working_directory,
                                                           filename=name,
                                                           semantic_type=semantic_type,
                                                           planned_time=time.time(),
                                                           mime_type="null")

                # Read metadata to associate with this input file
                metadata_parser = configparser.ConfigParser()
                metadata_parser.read(filenames="{}.metadata.cfg".format(input_full_path))

                # Import input file into the task database
                task_db.file_version_register(product_id=product_id,
                                              generated_by_task_execution=parent_attempt_id,
                                              file_path_input=input_full_path,
                                              preserve=True,
                                              metadata=dict(metadata_parser['metadata']),
                                              passed_qc=True
                                              )
                task_description['inputs'][semantic_type] = name

        # Dictionary of metadata to input into this task
        task_metadata = {
            'task_description': json.dumps(task_description)
        }

        # Create task entry in database
        new_task_id = task_db.task_register(task_type=task_type,
                                            working_directory=working_directory,
                                            job_name=job_name,
                                            task_name=task_name,
                                            metadata=task_metadata
                                            )

        # Create file product placeholders for all output files
        if 'outputs' in config_parser:
            for semantic_type, output_filename in config_parser['outputs'].items():
                logging.info("Create placeholder output <{}> -> <{}>".format(semantic_type, output_filename))

                # Create file product entry for this output file
                name = os.path.split(output_filename)[1]
                task_db.file_product_register(generator_task=new_task_id,
                                              directory=working_directory,
                                              filename=name,
                                              semantic_type=semantic_type,
                                              planned_time=time.time(),
                                              mime_type="null")

        # Mark all tasks as fully configured and ready to run
        task_db.db_handle.parameterised_query("UPDATE eas_task SET isFullyConfigured=1;")

    # Add the task to the job queue
    with task_queues.TaskScheduler() as scheduler:
        scheduler.schedule_a_task(task_id=new_task_id)

    # Actually run the task
    enter_service_mode(db_engine=db_engine, db_user=db_user, db_passwd=db_passwd, db_host=db_host,
                       db_port=db_port, db_name=db_database,
                       queue_implementation=queue_implementation,
                       mq_user=mq_user, mq_passwd=mq_passwd, mq_host=mq_host, mq_port=mq_port,
                       infinite_loop=False)

    # Display output metadata
    with task_database.TaskDatabaseConnection() as task_db:
        output_metadata = task_db.metadata_fetch_all(scheduling_attempt_id=new_task_id)
        logging.info("Output metadata:")
        for metadata_key in sorted(output_metadata.keys()):
            logging.info("{:32s}: {}".format(metadata_key, output_metadata[metadata_key].value))


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
