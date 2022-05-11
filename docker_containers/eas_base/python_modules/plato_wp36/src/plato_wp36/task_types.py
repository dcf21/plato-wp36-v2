# -*- coding: utf-8 -*-
# task_types.py

"""
Module for reading the list of all known pipeline tasks, and the list of which Docker containers are capable
of running each type of task.
"""

import os

from typing import Dict, Optional, Set

from .settings import Settings
from .vendor import xmltodict


class TaskTypeList:
    """
    Class for reading and representing the list of all known pipeline tasks, and the list of which Docker containers
    are capable of running each type of task.
    """

    def __init__(self):
        """
        Initialise a null list of known pipeline tasks.
        """

        # List of all known Docker containers
        self.container_names: Set[str] = set()

        # List of all known pipeline tasks, mapped to the set of Docker containers capable of running them
        self.task_list: Dict[str, Set[str]] = {}

        # List of all known Docker containers, mapped to the set of tasks they can perform
        self.container_capabilities: Dict[str, Set[str]] = {}

    def task_names(self):
        """
        Return a list of all known task names.
        :return:
            List of all known task names.
        """

        return self.task_list.keys()

    def containers_for_task(self, task_name: str):
        """
        Return a list of the names of the Docker containers which are capable of running a particular task.

        :param task_name:
            The name of the task to be run
        :type task_name:
            str
        :return:
            List of string names of Docker containers
        """

        return self.task_list[task_name]

    def tasks_for_container(self, container_name: str):
        """
        Return a list of the names of the task types that a named type of Docker container can run.

        :param container_name:
            The name of the Docker container
        :type container_name:
            str
        :return:
            List of string names of tasks the Docker container can run
        """

        return self.container_capabilities[container_name]

    @classmethod
    def read_from_xml(cls, xml_filename: Optional[str] = None):
        """
        Read the contents of an XML file specifying the list of all known pipeline tasks.

        :param xml_filename:
            The filename of the XML file specifying the list of all known pipeline tasks.
        :type xml_filename:
            str
        :return:
            TaskTypeList instance
        """

        # Fetch EAS settings
        settings = Settings().settings

        # Default path for the XML file
        if xml_filename is None:
            xml_filename = os.path.join(settings['pythonPath'], 'task_type_registry.xml')

        # Read contents of XML file
        with open(xml_filename, "rb") as in_stream:
            xml_structure = xmltodict.parse(xml_input=in_stream)['task_type_registry']

        # Start building task list
        output: TaskTypeList = TaskTypeList()

        # Parse list of Docker containers
        for container_item in xml_structure['containers']['container']:
            container_name = container_item['name']
            output.container_names.add(container_name)
            output.container_capabilities[container_name] = set()

        # Parse list of known pipeline tasks
        for task_item in xml_structure['tasks']['task']:
            task_name: str = task_item['name']
            docker_containers: Set[str] = set()

            # If we only have a list of one container type, still make sure it's a one-item list
            container_list = task_item['container']
            if isinstance(container_list, str):
                container_list = [container_list]

            # Compile a list of all the containers that can run this task
            for container_item in container_list:
                if container_item == "all":
                    # Special container name 'all' indicates that task is available in all containers
                    docker_containers = docker_containers.union(output.container_names)
                else:
                    # Make sure this container name is recognised
                    assert container_item in output.container_names, \
                        "Unrecognised container <{}>".format(container_item)

                    # Add container to list of those that can run this task
                    docker_containers.add(container_item)
                    output.container_capabilities[container_item].add(task_name)

            output.task_list[task_name] = docker_containers

        # Return new task list
        return output
