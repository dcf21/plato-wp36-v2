#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# deploy.py

"""
Creates a Kubernetes deployment of the EAS pipeline. Currently, we fork the kubectl commandline tool rather than
using the Python API because it's massively less verbose.
"""

import argparse
import os
import logging
import re
import sys
from typing import Iterable

from plato_wp36 import temporary_directory, task_database


def fetch_component_list():
    """
    Fetch a list of all the Kubernetes infrastructure elements which make up a deployment of the EAS pipeline.
    """

    # Name of the text file containing a list of the Kubernetes elements
    component_list_file = os.path.join(os.path.dirname(__file__), "kubernetes_resource_list.dat")
    kubernetes_components = []

    # Iterate through the text file, line by line
    with open(component_list_file) as f:
        for line in f:
            # Ignore comment lines
            line = line.strip()
            if len(line) < 1 or line[0] == '#':
                continue

            # Non-comment lines contain named infrastructure elements, one per line
            kubernetes_components.append(line)

    # Add a list of all the worker container types
    with task_database.TaskDatabaseConnection() as task_db:
        task_type_list = task_db.task_type_list_from_db()
        for container_name in task_type_list.worker_containers:
            if container_name not in kubernetes_components:
                deployment_name = re.sub("_", "-", container_name)
                kubernetes_components.append(deployment_name)

    # Return a list of all the infrastructure elements that we found
    return kubernetes_components


def deploy_all(namespace: str, worker_types: Iterable):
    """
    Deploy all the Kubernetes infrastructure items needed by the EAS pipeline.

    :param namespace:
        The Kubernetes namespace in which to deploy the items.
    :param worker_types:
        A list of all the types of worker nodes that are to be deployed.
    """
    # Create namespace for the EAS resources
    create_namespace(namespace=namespace)

    # List of components in the order in which we create them
    components = fetch_component_list()

    # Create components in order
    for item in components:
        # Work out whether this item is needed. We may not deploy all worker types, unless requested by the user
        item_needed = True
        if item.startswith("eas-worker-") and item not in worker_types:
            item_needed = False

        # If this component is needed, deploy it now
        if item_needed:
            deploy_or_delete_item(item_name=item, namespace=namespace)


def create_namespace(namespace: str):
    """
    Create a single namespace within Kubernetes (if it doesn't already exist).

    :param namespace:
        The name of the namespace to create.
    """
    os.system("kubectl create namespace {}".format(namespace))


def deploy_or_delete_item(item_name: str, namespace: str, delete: bool = False):
    """
    Deploy a single infrastructure item within Kubernetes, as described by a YAML file on disk.

    :param item_name:
        The filename of the YAML file describing the infrastructure item to deploy.
    :param namespace:
        The Kubernetes namespace in which to deploy the item.
    :param delete:
        Boolean. If true, then delete an infrastructure item, rather than deploying it
    """

    if not delete:
        logging.info("Creating <{}>".format(item_name))
        kubernetes_action = "apply"
    else:
        logging.info("Deleting <{}>".format(item_name))
        kubernetes_action = "delete"

    if not item_name.strip("eas-worker-"):
        yaml_filename = os.path.join(os.path.dirname(__file__), "../kubernetes_yaml", "{}.yaml".format(item_name))
        os.system("kubectl {} -f {} -n={}".format(kubernetes_action, yaml_filename, namespace))
    else:
        # Look up resource requirements for this EAS worker type
        container_name = re.sub("-", "_", item_name)
        with task_database.TaskDatabaseConnection() as task_db:
            task_type_list = task_db.task_type_list_from_db()
            assert container_name in task_type_list.worker_containers, \
                "Unknown worker type <{}>".format(container_name)
            resource_requirements = task_type_list.worker_containers[container_name]

        yaml_filename = os.path.join(os.path.dirname(__file__), "../kubernetes_yaml/eas-worker-template.yaml")
        yaml_template = open(yaml_filename).read()
        yaml_descriptor = yaml_template.format(
            pod_name=item_name,
            container_name=container_name,
            memory_requirement=resource_requirements['memory'],
            cpu_requirement=resource_requirements['cpu'],
            gpu_requirement=resource_requirements['gpu']
        )

        with temporary_directory.TemporaryDirectory() as tmp_dir:
            # Write out YAML description for this pod deployment
            yaml_path = os.path.join(tmp_dir.tmp_dir, "item.yaml")

            with open(yaml_path, "wt") as f:
                f.write(yaml_descriptor)

            # Deploy this item
            os.system("kubectl {} -f {} -n={}".format(kubernetes_action, yaml_path, namespace))


# If we're called as a script, deploy straight away
if __name__ == '__main__':
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--namespace', default="plato", type=str, dest='namespace',
                        help='The Kubernetes namespace to deploy the EAS pipeline into.')
    parser.add_argument('--worker', action='append', type=str, dest='worker',
                        help='The name of a worker node type that we should deploy.')
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S')
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # Build list of workers we are to deploy
    worker_types = args.worker
    if worker_types is None:
        worker_types = ()

    # Do deployment
    deploy_all(namespace=args.namespace, worker_types=worker_types)
