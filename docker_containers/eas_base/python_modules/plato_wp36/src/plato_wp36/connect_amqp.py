# -*- coding: utf-8 -*-
# connect_amqp.py

"""
Module for connecting to AMQP-based job queue.
"""

import os

from .settings import Settings


class MessageQueueConnector:
    """
    Class for connecting to AMQP-based job queue.
    """

    def __init__(self):
        pass

    @staticmethod
    def amqp_login_config_path():
        """
        Path to RabbitMQ configuration file with username and password.

        :return:
            str
        """

        # Fetch EAS settings
        settings = Settings().settings

        python_config = os.path.join(settings['pythonPath'], "../../data/datadir_local/local_settings_amqp.conf")

        return python_config

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
