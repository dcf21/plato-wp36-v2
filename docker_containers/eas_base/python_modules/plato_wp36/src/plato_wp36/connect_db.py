# -*- coding: utf-8 -*-
# connect_db.py

"""
Module for connecting to MySQL database for storage of results.
"""

# Ignore SQL warnings
import warnings
import MySQLdb
import os
import re
import sqlite3

from typing import Optional

from .settings import Settings

warnings.filterwarnings("ignore", ".*Unknown table .*")


class DatabaseInterface:
    """
    Class defining a unified interface for interacting with SQL databases.
    """

    def __init__(self):
        """
        Initialise a connection to the SQL database.
        """
        self.db = None
        self.db_cursor = None

    def __enter__(self):
        """
        Allow this class to be used within a with block.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called upon exit from a with class
        """
        self.commit()
        self.close()

    def __del__(self):
        """
        Close database connection
        """
        self.close()

    def test_database_exists(self):
        """
        Test whether the task database has already been set up.

        :return:
            Boolean indicating whether the database has been set up
        """
        raise NotImplementedError

    def create_database(self):
        """
        Create a clean database.
        """
        raise NotImplementedError

    def connect(self):
        """
        Open a connection to the SQL database.
        """
        raise NotImplementedError

    @staticmethod
    def sql_login_config_path(engine_name: str):
        """
        Fetch the path to SQL configuration file with username and password that we use for future connections.

        :return:
            List[str]
        """

        # Fetch EAS settings
        settings = Settings().settings

        mysql_config = os.path.join(settings['pythonPath'],
                                    "../../data/datadir_local/{}_sql_login.cfg".format(engine_name))
        python_config = os.path.join(settings['pythonPath'],
                                     "../../data/datadir_local/local_settings_sql.conf")

        return mysql_config, python_config

    def make_sql_login_config(self):
        """
        Create SQL configuration file with default username and password, which means we can log into database without
        supplying these when we try to connect to the database in the future.

        :return:
            None
        """
        raise NotImplementedError

    def commit(self):
        """
        Commit changes to the database.
        """
        raise NotImplementedError

    def close(self):
        """
        Close connection to the database.
        """
        raise NotImplementedError

    def parameterised_query(self, sql: str, parameters: Optional[tuple] = None):
        """
        Execute a database query with a single set of input parameters.
        """
        raise NotImplementedError

    def parameterised_query_many(self, sql: str, parameters: Optional[tuple] = None):
        """
        Execute a database query with multiple sets of input parameters.
        """
        raise NotImplementedError

    def fetchall(self):
        """
        Fetch all results.
        """
        return self.db_cursor.fetchall()

    def fetchone(self):
        """
        Fetch a single result.
        """
        return self.db_cursor.fetchone()

    def lastrowid(self):
        """
        Fetch the ID of the last inserted row.
        """
        return self.db_cursor.lastrowid


class DatabaseInterfaceMySql(DatabaseInterface):
    """
    Class defining an interface for interacting with MySQL databases.
    """

    def __init__(self, db_user: Optional[str] = None, db_passwd: Optional[str] = None,
                 db_host: Optional[str] = None, db_port: Optional[int] = None,
                 db_database: Optional[str] = None):
        """
        Initialise a connection to the SQL database.

        :param db_database:
            The name of the database we should connect to
        :param db_user:
            The name of the database user
        :param db_passwd:
            The password for the database user
        :param db_host:
            The host on which the database server is running
        :param db_port:
            The port on which the database server is running
        """

        # Run constructor of parent class
        super(DatabaseInterfaceMySql, self).__init__()

        # Fetch EAS settings
        settings = Settings()

        # Look up default MySQL database log in details
        self.db_host = settings.installation_info['db_host']
        self.db_port = int(settings.installation_info['db_port'])
        self.db_user = settings.installation_info['db_user']
        self.db_password = settings.installation_info['db_password']
        self.db_database = settings.installation_info['db_database']

        # Substitute any manually-overridden connection details
        if db_user is not None:
            self.db_user = db_user
        if db_passwd is not None:
            self.db_password = db_passwd
        if db_host is not None:
            self.db_host = db_host
        if db_port is not None:
            self.db_port = db_port
        if db_database is not None:
            self.db_database = db_database

    def test_database_exists(self):
        """
        Test whether the task database has already been set up.

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

    def create_database(self):
        """
        Create an empty SQL database.
        """

        # Read database schema
        pwd = os.path.split(os.path.abspath(__file__))[0]
        sql = os.path.join(pwd, "task_database_schema.sql")
        db_config_filename = self.sql_login_config_path(engine_name="mysql")[0]

        # Create mysql login config file
        self.make_sql_login_config()

        # Recreate database from scratch
        cmd = "echo 'DROP DATABASE IF EXISTS {:s};' | mysql --defaults-extra-file={:s}".format(self.db_database,
                                                                                               db_config_filename)
        os.system(cmd)
        cmd = ("echo 'CREATE DATABASE {:s} CHARACTER SET utf8mb4;' | mysql --defaults-extra-file={:s}".
               format(self.db_database, db_config_filename))
        os.system(cmd)

        # Create basic database schema
        cmd = "cat {:s} | mysql --defaults-extra-file={:s} {:s}".format(sql, db_config_filename, self.db_database)
        os.system(cmd)

    def connect(self):
        """
        Open a connection to the SQL database.
        """

        if self.db is not None:
            self.close()

        self.db = MySQLdb.connect(host=self.db_host, port=self.db_port,
                                  user=self.db_user, passwd=self.db_password,
                                  db=self.db_database)
        self.db_cursor = self.db.cursor(cursorclass=MySQLdb.cursors.DictCursor)

        # Configure MySQL to use UTF8 character set
        self.db.set_character_set('utf8mb4')
        self.db_cursor.execute('SET NAMES utf8mb4;')
        self.db_cursor.execute('SET CHARACTER SET utf8mb4;')
        self.db_cursor.execute('SET character_set_connection=utf8mb4;')

    def make_sql_login_config(self):
        """
        Create SQL configuration file with username and password, which means we can log into database without
        supplying these on the command line.

        :return:
            None
        """

        mysql_config, python_config = self.sql_login_config_path(engine_name="mysql")

        # Write config file for MySQL
        config_text = """
[client]
user = {:s}
password = {:s}
host = {:s}
port = {:d}
default-character-set = utf8mb4
""".format(self.db_user, self.db_password, self.db_host, self.db_port)

        with open(mysql_config, "w") as f:
            f.write(config_text)

        # Write config file that the plato_wp36 Python settings module uses
        config_text = """
# MySQL database settings
db_engine: mysql
db_host: {:s}
db_port: {:d}
db_user: {:s}
db_password: {:s}
db_database: {:s}
""".format(self.db_host, self.db_port, self.db_user, self.db_password, self.db_database)

        with open(python_config, "w") as f:
            f.write(config_text)

    def commit(self):
        """
        Commit changes to the database.
        """
        if self.db is not None:
            self.db.commit()

    def close(self):
        """
        Close connection to the database.
        """
        if self.db is not None:
            self.db.close()
            self.db = None
            self.db_cursor = None

    def parameterised_query(self, sql: str, parameters: Optional[tuple] = None):
        """
        Execute a database query with a single set of input parameters.
        """
        self.db_cursor.execute(sql, parameters)

    def parameterised_query_many(self, sql: str, parameters: Optional[tuple] = None):
        """
        Execute a database query with multiple sets of input parameters.
        """
        self.db_cursor.executemany(sql, parameters)


class DatabaseInterfaceSqlite(DatabaseInterface):
    """
    Class defining an interface for interacting with sqlite3 databases.
    """

    def __init__(self, db_database: Optional[str] = None):
        """
        Initialise a connection to the SQL database.
        """

        # Run constructor of parent class
        super(DatabaseInterfaceSqlite, self).__init__()

        # Fetch EAS settings
        settings = Settings()

        # Look up default MySQL database log in details
        self.db_database = settings.installation_info['db_database']

        # Substitute manually-overridden connection details
        if db_database is not None:
            self.db_database = db_database

    def _sqlite3_database_path(self):
        """
        Return the path to the file containing the sqlite3 database
        """

        # Fetch EAS settings
        settings = Settings().settings

        return os.path.join(settings['pythonPath'],
                            "../../data/datadir_local/sqlite3_{}.db".format(self.db_database))

    def test_database_exists(self):
        """
        Test whether the task database has already been set up.

        :return:
            Boolean indicating whether the database has been set up
        """
        return os.path.isfile(path=self._sqlite3_database_path())

    def create_database(self):
        """
        Create an empty SQL database.
        """

        # Read database schema
        pwd = os.path.split(os.path.abspath(__file__))[0]
        sql_schema_file = os.path.join(pwd, "task_database_schema.sql")
        sql_schema = open(sql_schema_file).read()

        # Create sql login config file
        self.make_sql_login_config()

        # Recreate database from scratch
        db_file_path = self._sqlite3_database_path()
        if os.path.exists(db_file_path):
            os.unlink(path=db_file_path)

        # Create basic database schema
        # SQLite databases work faster if primary keys don't auto increment, so remove keyword from schema
        db = sqlite3.connect(db_file_path)
        c = db.cursor()
        schema = re.sub("AUTO_INCREMENT", "", sql_schema)
        c.executescript(schema)
        db.commit()
        db.close()

    def connect(self):
        """
        Open a connection to the SQL database.
        """

        # Return results as an associative array
        def dict_factory(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        # Close any pre-existing database connection
        if self.db is not None:
            self.db.close()

        # Open new database connection, and use custom row factory to get results as associative array
        db_file_path = self._sqlite3_database_path()
        self.db = sqlite3.connect(db_file_path)
        self.db.row_factory = dict_factory
        self.db_cursor = self.db.cursor()

    def make_sql_login_config(self):
        """
        Create SQL configuration file with username and password, which means we can log into database without
        supplying these on the command line.

        :return:
            None
        """

        sql_config, python_config = self.sql_login_config_path(engine_name="mysql")

        # Write config file for sqlite
        config_text = """
this file is reserved for future use
"""

        with open(sql_config, "w") as f:
            f.write(config_text)

        # Write config file that the plato_wp36 Python settings module uses
        config_text = """
# sqlite3 database settings
db_engine: sqlite3
db_database: {:s}
""".format(self.db_database)

        with open(python_config, "w") as f:
            f.write(config_text)

    def commit(self):
        """
        Commit changes to the database.
        """
        if self.db is not None:
            self.db.commit()

    def close(self):
        """
        Close connection to the database.
        """
        if self.db is not None:
            self.db.close()
            self.db = None
            self.db_cursor = None

    def parameterised_query(self, sql: str, parameters: Optional[tuple] = None):
        """
        Execute a database query with a single set of input parameters.
        """

        # Keep sqlite3 happy, even if there are no parameters
        if parameters is None:
            parameters = ()

        # sqlite3 uses ? as a placeholder for SQL parameters, not %s
        sql = re.sub(r"%s", r"?", sql)
        self.db_cursor.execute(sql, parameters)

    def parameterised_query_many(self, sql, parameters: Optional[tuple] = None):
        """
        Execute a database query with multiple sets of input parameters.
        """

        # sqlite3 uses ? as a placeholder for SQL parameters, not %s
        sql = re.sub(r"%s", r"?", sql)
        self.db_cursor.executemany(sql, parameters)


class DatabaseConnector:
    """
    Factory class for creating connections to SQL databases.
    """

    def __init__(self, db_engine: Optional[str] = None,
                 db_user: Optional[str] = None, db_passwd: Optional[str] = None,
                 db_host: Optional[str] = None, db_port: Optional[int] = None,
                 db_database: Optional[str] = None):
        """
        Factory for new connections to the database as DatabaseInterface objects.

        :param db_engine:
            The name of the SQL database engine we are using. Either <mysql> or <sqlite3>.
        :param db_database:
            The name of the database we should connect to
        :param db_user:
            The name of the database user (not used by sqlite3)
        :param db_passwd:
            The password for the database user (not used by sqlite3)
        :param db_host:
            The host on which the database server is running (not used by sqlite3)
        :param db_port:
            The port on which the database server is running (not used by sqlite3)
        :return:
            List of [database handle, connection handle]
        """

        # Fetch EAS settings
        settings = Settings()

        # Look up default SQL database connection details
        self.db_database = settings.installation_info['db_database']
        self.db_engine = settings.installation_info['db_engine']
        self.db_host = settings.installation_info['db_host']
        self.db_port = int(settings.installation_info['db_port'])
        self.db_user = settings.installation_info['db_user']
        self.db_password = settings.installation_info['db_password']

        # Override defaults
        if db_engine is not None:
            self.db_engine = db_engine
        if db_user is not None:
            self.db_user = db_user
        if db_passwd is not None:
            self.db_password = db_passwd
        if db_host is not None:
            self.db_host = db_host
        if db_port is not None:
            self.db_port = db_port
        if db_database is not None:
            self.db_database = db_database

    def __enter__(self):
        """
        Called at the start of a with block
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Called at the end of a with block
        """
        pass

    def connect_db(self):
        """
        Return a new connection to the database as a DatabaseInterface object.

        :return:
            Instance of DatabaseInterface
        """

        if self.db_engine == "mysql":
            return DatabaseInterfaceMySql(db_user=self.db_user, db_passwd=self.db_password,
                                          db_host=self.db_host, db_port=self.db_port,
                                          db_database=self.db_database)
        elif self.db_engine == "sqlite3":
            return DatabaseInterfaceSqlite(db_database=self.db_database)
        else:
            raise ValueError("Unknown database engine <{}>".format(self.db_engine))
