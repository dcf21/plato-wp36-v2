# -*- coding: utf-8 -*-
# connect_db.py

"""
Module for connecting to MySQL database for storage of results.
"""

# Ignore SQL warnings
import warnings

import MySQLdb
import os

from .settings import Settings

warnings.filterwarnings("ignore", ".*Unknown table .*")


class DatabaseConnector:
    """
    Class for connecting to MySQL database
    """

    def __init__(self):
        # Fetch testbench settings
        settings = Settings()

        # Look up MySQL database log in details
        self.db_host = settings.installation_info['db_host']
        self.db_port = int(settings.installation_info['db_port'])
        self.db_user = settings.installation_info['db_user']
        self.db_password = settings.installation_info['db_password']
        self.db_database = settings.installation_info['db_database']

    def test_database_exists(self):
        """
        Test whether the status database has already been set up.

        :return:
            Boolean indicating whether the database has been set up
        """

        try:
            db = MySQLdb.connect(host=self.db_host, port=self.db_port,
                                 user=self.db_user, passwd=self.db_password,
                                 db=self.db_database)
        except MySQLdb._exceptions.OperationalError as exception:
            if "Unknown database" not in str(exception):
                raise
            return False

        db.close()
        return True

    @staticmethod
    def mysql_login_config_path():
        """
        Path to MySQL configuration file with username and password.

        :return:
            List[str]
        """

        # Fetch testbench settings
        settings = Settings().settings

        mysql_config = os.path.join(settings['pythonPath'], "../../data/datadir_local/mysql_login.cfg")
        python_config = os.path.join(settings['pythonPath'], "../../data/datadir_local/local_settings_mysql.conf")

        return mysql_config, python_config

    @staticmethod
    def amqp_login_config_path():
        """
        Path to RabbitMQ configuration file with username and password.

        :return:
            str
        """

        # Fetch testbench settings
        settings = Settings().settings

        python_config = os.path.join(settings['pythonPath'], "../../data/datadir_local/local_settings_amqp.conf")

        return python_config

    def make_mysql_login_config(self, db_user: str, db_passwd: str, db_host: str, db_port: int, db_database: str):
        """
        Create MySQL configuration file with username and password, which means we can log into database without
        supplying these on the command line.

        :return:
            None
        """

        mysql_config, python_config = self.mysql_login_config_path()

        # Write config file for MySQL
        config_text = """
[client]
user = {:s}
password = {:s}
host = {:s}
port = {:d}
default-character-set = utf8mb4
""".format(db_user, db_passwd, db_host, db_port)

        with open(mysql_config, "w") as f:
            f.write(config_text)

        # Write config file that the plato_wp36 Python settings module uses
        config_text = """
# MySQL database settings
db_host: {:s}
db_port: {:d}
db_user: {:s}
db_password: {:s}
db_database: {:s}
""".format(db_host, db_port, db_user, db_passwd, db_database)

        with open(python_config, "w") as f:
            f.write(config_text)

    def make_amqp_login_config(self, mq_user: str, mq_passwd: str, mq_host: str, mq_port: int):
        """
        Create configuration file with the message bus username and password, which means we connect in the future
        without supplying these on the command line.

        :return:
            None
        """

        python_config = self.amqp_login_config_path()

        # Write config file that the plato_wp36 Python settings module uses
        config_text = """
# RabbitMQ database settings
mq_host: {:s}
mq_port: {:d}
mq_user: {:s}
mq_password: {:s}
""".format(mq_host, mq_port, mq_user, mq_passwd)

        with open(python_config, "w") as f:
            f.write(config_text)

    def connect_db(self, database=None):
        """
        Return a new MySQLdb connection to the database.

        :param database:
            The name of the database we should connect to
        :return:
            List of [database handle, connection handle]
        """

        if database is None:
            database = self.db_database

        db = MySQLdb.connect(host=self.db_host, port=self.db_port,
                             user=self.db_user, passwd=self.db_password,
                             db=database)
        c = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        db.set_character_set('utf8mb4')
        c.execute('SET NAMES utf8mb4;')
        c.execute('SET CHARACTER SET utf8mb4;')
        c.execute('SET character_set_connection=utf8mb4;')

        return db, c
