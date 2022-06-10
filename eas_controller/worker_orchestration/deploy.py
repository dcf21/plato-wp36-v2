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
import multiprocessing
import psutil
import re
import sys
from typing import Iterable, Optional

from plato_wp36 import settings, temporary_directory, task_database

def item_is_worker(item_name: str):
    """
    Test if an infrastructure element is core infrastructure (always deployed), or a worker node that we scale
    according to demand

    :param item_name:
        The name of the Docker container to query
    """
    return item_name.startswith("eas-worker-") or item_name == "eas-base"


def fetch_component_list(include_workers: bool = True):
    """
    Fetch a list of all the Kubernetes infrastructure elements which make up a deployment of the EAS pipeline.

    :param include_workers:
        If true, then include the worker pods in the list of Kubernetes components. Note that this isn't possible
        without an initialised database, so set to False if the database isn't initialised yet.
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
    if include_workers:
        with task_database.TaskDatabaseConnection() as task_db:
            task_type_list = task_db.task_type_list_from_db()
            for container_name in task_type_list.worker_containers:
                if container_name not in kubernetes_components:
                    deployment_name = re.sub("_", "-", container_name)
                    kubernetes_components.append(deployment_name)

    # Return a list of all the infrastructure elements that we found
    return kubernetes_components


def deploy_all(namespace: str, worker_types: Iterable, resource_limit_fraction: Optional[float] = None):
    """
    Deploy all the Kubernetes infrastructure items needed by the EAS pipeline.

    :param namespace:
        The Kubernetes namespace in which to deploy the items.
    :param worker_types:
        A list of all the types of worker nodes that are to be deployed.
    :param resource_limit_fraction:
        Limit workers to a given fraction of total system resources, even if they request more.
    :return:
        None
    """
    # Create namespace for the EAS resources
    create_namespace(namespace=namespace)

    # List of components in the order in which we create them
    components = fetch_component_list(include_workers=len(list(worker_types)) > 0)

    # Create components in order
    for item in components:
        # Work out whether this item is needed. We may not deploy all worker types, unless requested by the user
        item_needed = True
        if item_is_worker(item_name=item) and item not in worker_types:
            item_needed = False

        # If this component is needed, deploy it now
        if item_needed:
            deploy_or_delete_item(item_name=item, namespace=namespace, resource_limit_fraction=resource_limit_fraction)


def create_namespace(namespace: str):
    """
    Create a single namespace within Kubernetes (if it doesn't already exist).

    :param namespace:
        The name of the namespace to create.
    """
    os.system("kubectl create namespace {}".format(namespace))


def deploy_or_delete_item(item_name: str, namespace: str, delete: bool = False,
                          resource_limit_fraction: Optional[float] = None):
    """
    Deploy a single infrastructure item within Kubernetes, as described by a YAML file on disk.

    :param item_name:
        The filename of the YAML file describing the infrastructure item to deploy.
    :param namespace:
        The Kubernetes namespace in which to deploy the item.
    :param delete:
        Boolean. If true, then delete an infrastructure item, rather than deploying it
    :param resource_limit_fraction:
        Limit workers to a given fraction of total system resources, even if they request more.
    :return:
        None
    """

    # Fetch EAS pipeline settings
    s = settings.Settings()

    if not delete:
        logging.info("Creating <{}>".format(item_name))
        kubernetes_action = "apply"
    else:
        logging.info("Deleting <{}>".format(item_name))
        kubernetes_action = "delete"

    if not item_is_worker(item_name=item_name):
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

        # Limit resource request to requested fraction of total system resources
        cpu_request = resource_requirements['cpu']
        ram_request = resource_requirements['memory_gb']
        gpu_request = resource_requirements['gpu']

        if resource_limit_fraction is not None:
            cpu_max_request = multiprocessing.cpu_count() * resource_limit_fraction
            if cpu_request > cpu_max_request:
                logging.info("Limiting worker <{}> to {:.3f} cpu cores; request was {:.3f} cores".
                             format(container_name, cpu_max_request, cpu_request))
                cpu_request = cpu_max_request

            ram_max_request_gb = psutil.virtual_memory().total / pow(1024, 3) * resource_limit_fraction
            if ram_request > ram_max_request_gb:
                logging.info("Limiting worker <{}> to {:.3f} GB ram; request was {:.3f} GB".
                             format(container_name, ram_max_request_gb, ram_request))
                ram_request = ram_max_request_gb

        # Update database with resource assignment
        with task_database.TaskDatabaseConnection() as task_db:
            task_db.container_set_resource_assignment(container_name=container_name,
                                                      cpu=cpu_request,
                                                      gpu=gpu_request,
                                                      memory_gb=ram_request)

        # Create YAML string describing this worker deployment
        yaml_filename = os.path.join(os.path.dirname(__file__), "../kubernetes_yaml/eas-worker-template.yaml")
        yaml_template = open(yaml_filename).read()
        yaml_descriptor = yaml_template.format(
            pod_name=item_name,
            container_name=container_name,
            memory_requirement="{:.0f}Mi".format(ram_request * 1024),
            cpu_requirement=cpu_request,
            gpu_requirement=gpu_request,
            db_engine=s.installation_info['db_engine'],
            db_user=s.installation_info['db_user'],
            db_passwd=s.installation_info['db_password'],
            db_host=s.installation_info['db_host'],
            db_port=int(s.installation_info['db_port']),
            db_name=s.installation_info['db_database'],
            queue_implementation=s.installation_info['queue_implementation'],
            mq_user=s.installation_info['mq_user'],
            mq_passwd=s.installation_info['mq_password'],
            mq_host=s.installation_info['mq_host'],
            mq_port=int(s.installation_info['mq_port'])
        )

        # Save YAML description to file
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
    parser.add_argument('--limit-to-system-fraction', type=float, dest='resource_limit', default=0.25,
                        help='Limit workers to a given fraction of total system resources, even if they request more.')
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
    deploy_all(namespace=args.namespace, worker_types=worker_types, resource_limit_fraction=args.resource_limit)
