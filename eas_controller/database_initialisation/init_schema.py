#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# init_schema.py

import argparse
import logging
import os

from plato_wp36 import settings


def make_mysql_login_config(db_user: str, db_passwd: str, db_host: str, db_port: int, db_name: str):
    """
    Create MySQL configuration file with username and password, which means we can log into database without
    supplying these on the command line.

    :return:
        None
    """

    pwd = os.getcwd()
    db_config = os.path.join(pwd, "../../data/datadir_local/mysql_login.cfg")

    config_text = """
[client]
user = {:s}
password = {:s}
host = {:s}
port = {:d}
default-character-set = utf8mb4
""".format(db_user, db_passwd, db_host, db_port)
    open(db_config, "w").write(config_text)


def init_schema(db_user: str, db_passwd: str, db_host: str, db_port: int, db_name: str):
    """
    Create database tables, using schema defined in <schema.sql>.

    :return:
        None
    """

    pwd = os.getcwd()
    sql = os.path.join(pwd, "schema.sql")
    db_config = os.path.join(pwd, "../../data/datadir_local/mysql_login.cfg")

    # Create mysql login config file
    make_mysql_login_config(db_user=db_user, db_passwd=db_passwd,
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


# Do it right away if we're run as a script
if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db_user', default="plato", type=str, dest='db_user', help='Database user')
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
