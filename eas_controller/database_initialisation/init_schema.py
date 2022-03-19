#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# init_schema.py

"""
Create a set of empty database tables, initialising the schema of the results database.
"""

import argparse
import logging
import os

from plato_wp36 import connect_db, settings, task_database, task_types


def init_schema(db_user: str, db_passwd: str, db_host: str, db_port: int, db_name: str):
    """
    Create database tables, using schema defined in <schema.sql>.

    :return:
        None
    """

    # Instantiate database connection class
    db = connect_db.DatabaseConnector()

    # Read database schema
    pwd = os.path.split(os.path.abspath(__file__))[0]
    sql = os.path.join(pwd, "schema.sql")
    db_config = db.mysql_login_config_path()

    # Create mysql login config file
    db.make_mysql_login_config(db_user=db_user, db_passwd=db_passwd,
                               db_host=db_host, db_port=db_port)

    # Recreate database from scratch
    cmd = "echo 'DROP DATABASE IF EXISTS {:s};' | mysql --defaults-extra-file={:s}".format(db_name, db_config)
    os.system(cmd)
    cmd = ("echo 'CREATE DATABASE {:s} CHARACTER SET utf8mb4;' | mysql --defaults-extra-file={:s}".
           format(db_name, db_config))
    os.system(cmd)

    # Create basic database schema
    cmd = "cat {:s} | mysql --defaults-extra-file={:s} {:s}".format(sql, db_config, db_name)
    os.system(cmd)

    # Read list of known task types
    tasks = task_types.TaskTypeList.read_from_xml()

    # Write list of task types to the database
    task_db = task_database.TaskDatabaseConnection()
    task_db.task_list_to_db(task_list=tasks)


# Do it right away if we're run as a script
if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db_user', default="root", type=str, dest='db_user', help='Database user')
    parser.add_argument('--db_passwd', default="plato", type=str, dest='db_passwd', help='Database password')
    parser.add_argument('--db_host', default="localhost", type=str, dest='db_host', help='Database host')
    parser.add_argument('--db_port', default=30036, type=int, dest='db_port', help='Database port')
    parser.add_argument('--db_name', default="plato", type=str, dest='db_name', help='Database name')
    args = parser.parse_args()

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
    init_schema(db_user=args.db_user, db_passwd=args.db_passwd,
                db_host=args.db_host, db_port=args.db_port,
                db_name=args.db_name)
