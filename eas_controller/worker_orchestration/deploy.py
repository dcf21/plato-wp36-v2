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
import sys
from typing import Iterable
from kubernetes import config


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
    components = ["input-pv", "input-pvc", "output-pv", "output-pvc", "mysql-pv-minikube", "mysql-pvc-minikube",
                  "mysql-app", "mysql-service", "rabbitmq-controller", "rabbitmq-service", "eas-worker-base",
                  "web-interface", "web-interface-service"]

    # Create components in order
    for item in components:
        # Work out whether this item is needed. We may not deploy all worker types, unless requested by the user
        item_needed = True
        if item.startswith("eas-worker-") and item not in worker_types:
            item_needed = False

        # If this component is needed, deploy it now
        if item_needed:
            deploy_item(name=item, namespace=namespace)


def create_namespace(namespace: str):
    """
    Create a single namespace within Kubernetes (if it doesn't already exist).

    :param namespace:
        The name of the namespace to create.
    """
    os.system("kubectl create namespace {}".format(namespace))


def deploy_item(name: str, namespace: str):
    """
    Deploy a single infrastructure item within Kubernetes, as described by a YAML file on disk.

    :param name:
        The filename of the YAML file describing the infrastructure item to deploy.
    :param namespace:
        The Kubernetes namespace in which to deploy the item.
    """
    logging.info("Creating <{}>".format(name))
    config.load_kube_config()

    json_filename = os.path.join(os.path.dirname(__file__), "../kubernetes_yaml", "{}.yaml".format(name))

    os.system("kubectl apply -f {} -n={}".format(json_filename, namespace))


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

    # Do deployment
    deploy_all(namespace=args.namespace, worker_types=args.worker)
