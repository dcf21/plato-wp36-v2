# -*- coding: utf-8 -*-
# connect_db.py

"""
Module for connecting to MySQL database for storage of results.
"""

# Ignore SQL warnings
import warnings

import MySQLdb
import os

from .settings import settings, installation_info

warnings.filterwarnings("ignore", ".*Unknown table .*")


class DatabaseConnector:
    """
    Class for connecting to MySQL database
    """

    def __init__(self):
        # Look up MySQL database log in details
        self.db_host = installation_info['db_host']
        self.db_user = installation_info['db_user']
        self.db_password = installation_info['db_password']
        self.db_database = installation_info['db_database']

    def test_database_exists(self):
        """
        Test whether the status database has already been set up.

        :return:
            Boolean indicating whether the database has been set up
        """

        try:
            db = MySQLdb.connect(host=self.db_host, user=self.db_user, passwd=self.db_password, db=self.db_database)
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
            str
        """
        return os.path.join(settings['pythonPath'], "../../data/datadir_local/mysql_login.cfg")

    def make_mysql_login_config(self, db_user: str, db_passwd: str, db_host: str, db_port: int):
        """
        Create MySQL configuration file with username and password, which means we can log into database without
        supplying these on the command line.

        :return:
            None
        """

        db_config = self.mysql_login_config_path()

        config_text = """
[client]
user = {:s}
password = {:s}
host = {:s}
port = {:d}
default-character-set = utf8mb4
""".format(db_user, db_passwd, db_host, db_port)
        open(db_config, "w").write(config_text)

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

        db = MySQLdb.connect(host=self.db_host, user=self.db_user, passwd=self.db_password, db=database)
        c = db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        db.set_character_set('utf8mb4')
        c.execute('SET NAMES utf8mb4;')
        c.execute('SET CHARACTER SET utf8mb4;')
        c.execute('SET character_set_connection=utf8mb4;')

        return db, c
