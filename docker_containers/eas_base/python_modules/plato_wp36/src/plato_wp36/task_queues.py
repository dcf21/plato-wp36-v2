# -*- coding: utf-8 -*-
# task_queues.py

"""
Python class for interacting with a message queue in RabbitMQ
"""

import json
import logging
import pika

from .settings import Settings


class TaskQueue:
    """
    Python class for interacting with a message queue in RabbitMQ.
    """

    def __init__(self, debugging: bool = False):
        """
        Establish a connection to message queue.

        :param debugging:
            If true, show verbose debugging messages from <pika>
        """

        # Set debugging level
        if debugging:
            logging.getLogger("pika").setLevel(logging.INFO)
        else:
            logging.getLogger("pika").setLevel(logging.WARNING)

        # Fetch testbench settings
        self.settings = Settings()

        # Look up MySQL database log in details
        self.mq_host = self.settings.installation_info['mq_host']
        self.mq_port = int(self.settings.installation_info['mq_port'])
        self.mq_user = self.settings.installation_info['mq_user']
        self.mq_password = self.settings.installation_info['mq_password']

        # Create AMQP access URL
        self.url = "amqp://{}:{}@{}:{}".format(
            self.mq_user, self.mq_password, self.mq_host, self.mq_port
        )

        # Connect to message queue
        self.connection = pika.BlockingConnection(pika.URLParameters(url=self.url))
        self.channel = self.connection.channel()

    def queue_declare(self, queue_name: str):
        """
        Declare a message queue on the AMQP server.

        :param queue_name:
            The name of the queue to declare
        :return:
            None
        """
        self.channel.queue_declare(queue=queue_name)

    def queue_length(self, queue_name: str):
        """
        Return the number of messages waiting in a message queue on the AMQP server.

        :param queue_name:
            The name of the queue to query
        :return:
            The number of messages waiting
        """
        queue_object = self.channel.queue_declare(queue=queue_name)
        queue_length = queue_object.method.message_count
        return queue_length

    def queue_publish(self, queue_name: str, message):
        """
        Publish a message to a message queue.

        :param queue_name:
            The name of the queue to send the message to.
        :param message:
            The object to send to the queue (will be JSON encoded before transmission).
        :return:
            None
        """
        json_message = json.dumps(message).encode('utf-8')
        # logging.info("Sending message <{}>".format(json_message))
        self.channel.basic_publish(exchange='', routing_key=queue_name, body=json_message)

    def queue_fetch(self, queue_name: str):
        """
        Fetch a message from a queue, without blocking.

        :param queue_name:
            The name of the queue to query
        :return:
            None
        """
        method_frame, header_frame, body = self.channel.basic_get(queue=queue_name)
        return method_frame, header_frame, body

    def message_ack(self, method_frame):
        """
        Acknowledge a message, so that it will not be resent to any other workers.

        :param method_frame:
            The frame of the message to be acknowledged.
        :return:
            None
        """
        self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)

    def close(self):
        """
        Close our connection to the message bus.

        :return:
            None
        """
        self.connection.close()
        self.connection = None
        self.channel = None
