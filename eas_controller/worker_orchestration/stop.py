#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# stop.py

"""
Stops a Kubernetes deployment of the test-bench. Currently fork the kubectl commandline tool rather than using the
Python API because it's massively less verbose.
"""

import argparse
import os
import logging
import sys


def delete_all(namespace: str):
    # List of components in the order in which we create them
    components = ["input-pv", "input-pvc", "output-pv", "output-pvc", "mysql-pv-minikube", "mysql-pvc-minikube",
                  "mysql-app", "mysql-service", "rabbitmq-controller", "rabbitmq-service", "eas-debugging"]

    # Delete components in the opposite order to which they are created
    for item in reversed(components):
        delete_item(name=item, namespace=namespace)


def delete_item(name: str, namespace: str):
    logging.info("Deleting <{}>".format(name))
    json_filename = os.path.join(os.path.dirname(__file__), "../kubernetes_yaml", "{}.yaml".format(name))
    os.system("kubectl delete -f {} -n={}".format(json_filename, namespace))


# If we're called as a script, deploy straight away
if __name__ == '__main__':
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--namespace', default="plato", type=str, dest='namespace',
                        help='The Kubernetes namespace to deploy the EAS pipeline into')
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S')
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # Delete cluster resources
    delete_all(namespace=args.namespace)
