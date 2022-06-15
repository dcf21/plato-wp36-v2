# -*- coding: utf-8 -*-
# task_queues.py

"""
Python class for interacting with a message queue in RabbitMQ or SQL.
"""

import logging
import os
import pika
import platform

from typing import Optional

from .settings import Settings
from .task_database import TaskDatabaseConnection


class TaskScheduler:
    """
    Python class for add tasks that are waiting to run into the job queue
    """

    def __init__(self, queue_implementation: Optional[str] = None):
        """
        :param queue_implementation:
            The name of the queue implementation we are using
        """

        # Fetch EAS settings
        settings = Settings()

        # Look up default MySQL database log in details
        self.queue_implementation = settings.installation_info['queue_implementation']

        # Substitute any manually-overridden connection details
        if queue_implementation is not None:
            self.queue_implementation = queue_implementation

    def __del__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def schedule_a_task(self, task_id: int):
        """
        Schedule a single task to run, by adding it to the job queue.

        :param task_id:
            The integer ID of the scheduling attempt to add to the job queue.
        """

        # Read metadata about this task from the task database
        with TaskDatabaseConnection() as task_db:
            # Fetch the name of the type of task
            task_db.db_handle.parameterised_query("""
SELECT t.taskId, ett.taskTypeName
FROM eas_task t
INNER JOIN eas_task_types ett on t.taskTypeId = ett.taskTypeId
WHERE t.taskId = %s;
""", (task_id,))
            tasks = task_db.db_handle.fetchall()

            # Open connection to the message queue
            with TaskQueueConnector(queue_engine=self.queue_implementation).interface() as message_bus:
                # Schedule each matching result
                for item in tasks:
                    queue_name = item['taskTypeName']
                    task_id = item['taskId']
                    logging.info("Scheduling {:6d} - {:s}".format(task_id, queue_name))
                    attempt_id = task_db.execution_attempt_register(task_id=task_id)
                    task_db.commit()
                    message_bus.queue_publish(queue_name=queue_name, item_id=attempt_id)

    def schedule_jobs_based_on_criterion(self, task_selection_criteria: str):
        """
        Schedule all tasks in the database which don't have any unfulfilled dependencies, and which don't have
        any previous run attempts which meet the database search criterion.

        :param task_selection_criteria:
            SQL criteria used to decide whether a previous run of a task means it shouldn't be run again.
        :return:
            None
        """

        # Read list of task types from the database
        with TaskDatabaseConnection() as task_db:
            # Fetch list of all the tasks to schedule
            # This is all tasks which do not have an existing scheduling attempt, and which also do not require
            # any file products which have not passed QC.
            task_db.db_handle.parameterised_query("""
SELECT t.taskId
FROM eas_task t
WHERE
  NOT EXISTS (SELECT 1 FROM eas_scheduling_attempt x WHERE x.taskId = t.taskId AND {})
    AND
  NOT EXISTS (SELECT 1 FROM eas_task_input y WHERE y.taskId = t.taskId
              AND NOT EXISTS (SELECT 1 FROM eas_product_version v WHERE v.productId = y.inputId AND v.passedQc))
    AND
  NOT EXISTS (SELECT 1 FROM eas_task_metadata_input z WHERE z.taskId = t.taskId
              AND NOT EXISTS
                (SELECT 1 FROM eas_scheduling_attempt a WHERE a.taskId = z.inputId AND a.allProductsPassedQc))
ORDER BY t.taskId;
""".format(task_selection_criteria))
            tasks = task_db.db_handle.fetchall()

            # Schedule each job in turn
            for item in tasks:
                self.schedule_a_task(task_id=item['taskId'])

    def schedule_all_waiting_jobs(self):
        """
        Schedule all tasks in the database which have not yet been queued.

        :return:
            None
        """

        # Don't re-run any task that we've run before
        self.schedule_jobs_based_on_criterion(task_selection_criteria="1")

    def reschedule_all_unfinished_jobs(self):
        """
        (Re)schedule all unfinished tasks to be (re)-run.

        :return:
            None
        """

        # Don't re-run any task that we've run before, where the task is still running and didn't have an error
        self.schedule_jobs_based_on_criterion(task_selection_criteria="x.isFinished AND NOT x.errorFail")


class TaskQueue:
    """
    Python class for describing an abstract job queue.
    """

    def __init__(self):
        self.connected = False

    def __del__(self):
        if self.connected:
            self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__del__()

    def queue_declare(self, queue_name: str):
        """
        Declare a task queue.

        :param queue_name:
            The name of the queue to declare
        :return:
            None
        """
        raise NotImplementedError

    def queue_length(self, queue_name: str):
        """
        Return the number of messages waiting in a task queue.

        :param queue_name:
            The name of the queue to query
        :return:
            The number of messages waiting
        """
        raise NotImplementedError

    def queue_publish(self, queue_name: str, item_id: int):
        """
        Publish a message to a task queue.

        :param queue_name:
            The name of the queue to send the message to.
        :param item_id:
            The integer ID of the scheduling attempt to put into the task queue
        :return:
            None
        """
        raise NotImplementedError

    def queue_fetch_and_acknowledge(self, queue_name: str, acknowledge: bool = True, set_running: bool = True):
        """
        Fetch a message from a queue, without blocking.

        :param queue_name:
            The name of the queue to query
        :param acknowledge:
            Flag indicating whether we acknowledge receipt of this item from the queue, preventing it from being
            delivered again.
        :param set_running:
            Flag indicating whether we mark this task as being running.
        :return:
            Scheduling attempt ID, or None if the queue is empty
        """
        raise NotImplementedError

    def queue_fetch_list(self, queue_name: str):
        """
        Fetch a list of all the items in a queue, without blocking.

        :param queue_name:
            The name of the queue to query
        :return:
            List of contents
        """
        raise NotImplementedError

    def close(self):
        """
        Close our connection to the task queue.

        :return:
            None
        """
        raise NotImplementedError


class TaskQueueAmqp(TaskQueue):
    """
    Python class for interacting with a message queue in RabbitMQ.
    """

    def __init__(self, debugging: bool = False):
        """
        Establish a connection to message queue.

        :param debugging:
            If true, show verbose debugging messages from <pika>
        """

        # Initialise parent class
        super().__init__()

        # Set debugging level
        if debugging:
            logging.getLogger("pika").setLevel(logging.INFO)
        else:
            logging.getLogger("pika").setLevel(logging.WARNING)

        # Fetch EAS settings
        self.settings = Settings()

        # Look up message queue log-in details
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

        # Connect to the task database
        self.db = TaskDatabaseConnection()
        self.connected = True

    def queue_declare(self, queue_name: str):
        """
        Declare a message queue on the AMQP server.

        :param queue_name:
            The name of the queue to declare
        :return:
            None
        """

        # Check that we are connected to the message queue
        assert self.connected

        # Declare message queue
        self.channel.queue_declare(queue=queue_name)

    def queue_length(self, queue_name: str):
        """
        Return the number of messages waiting in a message queue on the AMQP server.

        :param queue_name:
            The name of the queue to query
        :return:
            The number of messages waiting
        """

        # Check that we are connected to the message queue
        assert self.connected

        # Count number of queued items
        queue_object = self.channel.queue_declare(queue=queue_name)
        queue_length = queue_object.method.message_count
        return queue_length

    def queue_publish(self, queue_name: str, item_id: int):
        """
        Publish a message to a task queue.

        :param queue_name:
            The name of the queue to send the message to.
        :param item_id:
            The integer ID of the scheduling attempt to put into the task queue
        :return:
            None
        """

        # Check that we are connected to the message queue
        assert self.connected

        # Publish task into the job queue
        string_message = str(item_id).encode('utf-8')
        # logging.info("Sending message <{}>".format(json_message))
        self.channel.basic_publish(exchange='', routing_key=queue_name, body=string_message)

        # Update database to indicate that this task has been queued
        self.db.db_handle.parameterised_query("""
UPDATE eas_scheduling_attempt
SET isQueued=1, isRunning=0, isFinished=0, hostId=NULL
WHERE schedulingAttemptId=%s;
""", (item_id,))
        self.db.commit()

    def queue_fetch_and_acknowledge(self, queue_name: str, acknowledge: bool = True, set_running: bool = True):
        """
        Fetch a message from a queue, without blocking.

        :param queue_name:
            The name of the queue to query
        :param acknowledge:
            Flag indicating whether we acknowledge receipt of this item from the queue, preventing it from being
            delivered again.
        :param set_running:
            Flag indicating whether we mark this task as being running.
        :return:
            Scheduling attempt ID, or None if the queue is empty
        """

        # Check that we are connected to the message queue
        assert self.connected

        # Fetch an item from the message bus
        method_frame, header_frame, body = self.channel.basic_get(queue=queue_name)

        # Did we receive anything
        received_item = not (method_frame is None or method_frame.NAME == 'Basic.GetEmpty')

        # If we received an item, acknowledge it now so it will not be sent to other workers
        if received_item:
            if acknowledge:
                self.channel.basic_ack(delivery_tag=method_frame.delivery_tag)
            output_id = int(body)
        else:
            output_id = None

        # Return the item we fetched
        return output_id

    def queue_fetch_list(self, queue_name: str):
        """
        Fetch a list of all the items in a queue, without blocking.

        :param queue_name:
            The name of the queue to query
        :return:
            List of contents
        """

        # Check that we are connected to the message queue
        assert self.connected

        # Start compiling output list
        output = []

        while True:
            # Fetch an item from the message bus
            method_frame, header_frame, body = self.channel.basic_get(queue=queue_name)

            # Did we receive anything
            received_item = not (method_frame is None or method_frame.NAME == 'Basic.GetEmpty')

            # If we received an item, acknowledge it now so it will not be sent to other workers
            if received_item:
                output.append(int(body))
            else:
                break

        # Return the items we fetched
        return output

    def close(self):
        """
        Close our connection to the message bus.

        :return:
            None
        """
        if self.connected:
            self.connection.close()
            self.connection = None
            self.channel = None
            self.db.commit()
            self.db.close_db()
            self.db = None
        self.connected = False


class TaskQueueSQL(TaskQueue):
    """
    Python class for interacting with a message queue that is embedded into the task database.
    """

    def __init__(self):
        """
        Establish a connection to task database.
        """

        # Initialise parent class
        super().__init__()

        # Connect to the task database
        self.db = TaskDatabaseConnection()
        self.connected = True

    def queue_declare(self, queue_name: str):
        """
        Declare a message queue on the AMQP server.

        :param queue_name:
            The name of the queue to declare
        :return:
            None
        """

        # Check that we are connected to the message queue
        assert self.connected

        # No action required to declare a task queue in SQL
        return

    def queue_length(self, queue_name: str):
        """
        Return the number of messages waiting in a message queue on the AMQP server.

        :param queue_name:
            The name of the queue to query
        :return:
            The number of messages waiting
        """

        # Check that we are connected to the message queue
        assert self.connected

        # Count number of queued items
        self.db.db_handle.parameterised_query("""
SELECT COUNT(*)
FROM eas_scheduling_attempt s
INNER JOIN eas_task t ON t.taskId = s.taskId
INNER JOIN eas_task_types ty ON ty.taskTypeId = t.taskTypeId
WHERE ty.taskTypeName=%s AND s.isQueued;
""", (queue_name,))
        results = self.db.db_handle.fetchall()

        return results[0]['COUNT(*)']

    def queue_publish(self, queue_name: str, item_id: int):
        """
        Publish a message to a task queue.

        :param queue_name:
            The name of the queue to send the message to.
        :param item_id:
            The integer ID of the scheduling attempt to put into the task queue
        :return:
            None
        """

        # Check that we are connected to the message queue
        assert self.connected

        # Publish task into the job queue
        self.db.db_handle.parameterised_query("""
UPDATE eas_scheduling_attempt
SET isQueued=1, isRunning=0, isFinished=0, hostId=NULL
WHERE schedulingAttemptId=%s;
""", (item_id,))
        self.db.commit()

    def queue_fetch_and_acknowledge(self, queue_name: str, acknowledge: bool = True, set_running: bool = True):
        """
        Fetch a message from a queue, without blocking.

        :param queue_name:
            The name of the queue to query
        :param acknowledge:
            Flag indicating whether we acknowledge receipt of this item from the queue, preventing it from being
            delivered again.
        :param set_running:
            Flag indicating whether we mark this task as being running.
        :return:
            Scheduling attempt ID, or None if the queue is empty
        """

        # Check that we are connected to the message queue
        assert self.connected

        # Fetch our host identifier
        my_hostname = platform.node()
        host_id = self.db.hostname_get_id(name=my_hostname)

        # We are not currently run any tasks
        self.db.commit()
        self.db.db_handle.parameterised_query("""
UPDATE eas_scheduling_attempt
SET isRunning=0
WHERE hostId=%s;
""", (host_id,))
        self.db.commit()

        # Fetch an item from the job queue
        self.db.db_handle.parameterised_query("""
SELECT s.schedulingAttemptId
FROM eas_scheduling_attempt s
INNER JOIN eas_task t ON t.taskId = s.taskId
INNER JOIN eas_task_types ty ON ty.taskTypeId = t.taskTypeId
WHERE ty.taskTypeName=%s AND s.isQueued
ORDER BY s.queuedTime LIMIT 1;
""", (queue_name,))

        # Start running the item we took, but only if nobody else has marked it running first
        for item_id in self.db.db_handle.fetchall():
            self.db.db_handle.parameterised_query("""
UPDATE eas_scheduling_attempt
SET isQueued=0, isRunning=1, hostId=%s
WHERE schedulingAttemptId = %s AND isQueued;
""", (host_id, item_id['schedulingAttemptId']))
            self.db.commit()

        # Look up the integer ID of the item we got
        self.db.db_handle.parameterised_query("""
SELECT s.schedulingAttemptId
FROM eas_scheduling_attempt s
WHERE s.isRunning AND s.hostId=%s;
""", (host_id,))
        results = self.db.db_handle.fetchall()

        # Return the item we fetched
        if len(results) < 1:
            item_id = None
        else:
            item_id = results[0]['schedulingAttemptId']

        # If the user didn't want this item acknowledged and/or set running, put the item back into the queue
        if (item_id is not None) and ((not acknowledge) or (not set_running)):
            self.db.db_handle.parameterised_query("""
UPDATE eas_scheduling_attempt
SET isQueued=%s, isRunning=0, errorFail=%s, hostId=NULL
WHERE schedulingAttemptId = %s;
""", (int(not acknowledge), acknowledge, item_id))

        # Commit task table to reflect the job we have just taken
        self.db.commit()

        # Return item
        return item_id

    def queue_fetch_list(self, queue_name: str):
        """
        Fetch a list of all the items in a queue, without blocking.

        :param queue_name:
            The name of the queue to query
        :return:
            List of contents
        """

        # Check that we are connected to the message queue
        assert self.connected

        # Count number of queued items
        self.db.db_handle.parameterised_query("""
SELECT s.schedulingAttemptId
FROM eas_scheduling_attempt s
INNER JOIN eas_task t ON t.taskId = s.taskId
INNER JOIN eas_task_types ty ON ty.taskTypeId = t.taskTypeId
WHERE ty.taskTypeName=%s AND s.isQueued;
""", (queue_name,))
        results = self.db.db_handle.fetchall()

        return [item['schedulingAttemptId'] for item in results]

    def close(self):
        """
        Close our connection to the message bus.

        :return:
            None
        """
        if self.connected:
            self.db.commit()
            self.db.close_db()
            self.db = None
        self.connected = False


class TaskQueueConnector:
    """
    Factory class for creating connections to task queues.
    """

    def __init__(self, queue_engine: Optional[str] = None,
                 debugging: bool = False):
        """
        Factory for new connections to a task queue as TaskQueue objects.

        :param queue_engine:
            The name of the task queue implementation we are using. Either <amqp> or <sql>.
        :param debugging:
            Boolean indicating whether we want extensive debugging from AMQP.
        """

        # Fetch EAS settings
        settings = Settings()

        # Look up default SQL database connection details
        self.queue_engine = settings.installation_info['queue_implementation']
        self.debugging = False

        # Override defaults
        if queue_engine is not None:
            self.queue_engine = queue_engine
        if debugging is not None:
            self.debugging = debugging

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

    def interface(self):
        """
        Return a new connection to the task queue as a TaskQueue object.

        :return:
            Instance of TaskQueue
        """

        if self.queue_engine == "amqp":
            return TaskQueueAmqp(debugging=self.debugging)
        elif self.queue_engine == "sql":
            return TaskQueueSQL()
        else:
            raise ValueError("Unknown task queue implementation <{}>".format(self.queue_engine))

    @staticmethod
    def task_queue_config_path():
        """
        Path to task queue configuration file with task queue connection details.

        :return:
            str
        """

        # Fetch EAS pipeline settings
        settings = Settings().settings

        python_config = os.path.join(settings['pythonPath'], "../../data/datadir_local/local_settings_task_queue.conf")

        return python_config

    @staticmethod
    def make_task_queue_config(queue_implementation: str,
                               mq_user: str, mq_passwd: str, mq_host: str, mq_port: int):
        """
        Create configuration file with the message bus username and password, which means we connect in the future
        without supplying these on the command line.

        :param queue_implementation:
            The name of the task queue implementation we are using. Either <amqp> or <sql>.
        :param mq_user:
            The username to use when connecting to an AMQP-based task queue.
        :param mq_passwd:
            The password to use when connecting to an AMQP-based task queue.
        :param mq_host:
            The host to use when connecting to an AMQP-based task queue.
        :param mq_port:
            The port number to use when connecting to an AMQP-based task queue.
        :return:
            None
        """

        python_config = TaskQueueConnector.task_queue_config_path()

        # Write config file that the plato_wp36 Python settings module uses
        config_text = """
# Task queue implementation
queue_implementation: {:s}

# RabbitMQ database settings
mq_host: {:s}
mq_port: {:d}
mq_user: {:s}
mq_password: {:s}
""".format(queue_implementation, mq_host, mq_port, mq_user, mq_passwd)

        with open(python_config, "w") as f:
            f.write(config_text)
