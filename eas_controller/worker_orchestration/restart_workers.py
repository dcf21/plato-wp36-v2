#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# restart_workers.py

"""
Restart all the worker deployments in the Kubernetes cluster.
"""

import argparse
import logging
import subprocess
import sys

from typing import Optional

from deploy import deploy_or_delete_item


def get_list_of_running_workers(namespace: str):
    """
    Get a list of all the worker deployments currently on the Kubernetes cluster.

    :param namespace:
        The namespace that the EAS pipeline is running within.
    :return:
        List of deployment names
    """
    # Use kubectl to get a list of all deployments
    cmd = "kubectl get deployments -n={} --no-headers=true".format(namespace)
    proc = subprocess.run(cmd.split(), capture_output=True)
    kube_output_bytes = proc.stdout
    kube_output_str = kube_output_bytes.decode('utf-8')
    kube_output_lines = kube_output_str.strip().split('\n')

    # The name of the deployment is the first column of the table
    workers = [item.split()[0] for item in kube_output_lines if 'eas-worker-' in item]

    # Return list of deployments
    return workers


def restart_deployment(namespace: str, name: str, resource_limit_fraction: Optional[float] = None):
    """
    Restart a particular named worker deployment.

    :param namespace:
        The namespace that the EAS pipeline is running within.
    :param name:
        The name of the deployment to restart.
    :param resource_limit_fraction:
        Limit workers to a given fraction of total system resources, even if they request more.
    :return:
        None
    """

    deploy_or_delete_item(item_name=name, namespace=namespace, delete=True)
    deploy_or_delete_item(item_name=name, namespace=namespace, delete=False,
                          resource_limit_fraction=resource_limit_fraction)


# If we're called as a script, deploy straight away
if __name__ == '__main__':
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--namespace', default="plato", type=str, dest='namespace',
                        help='The Kubernetes namespace to deploy the EAS pipeline into.')
    parser.add_argument('--limit-to-system-fraction', type=float, dest='resource_limit', default=0.5,
                        help='Limit workers to a given fraction of total system resources, even if they request more.')
    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S')
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # Do restart
    for worker in get_list_of_running_workers(namespace=args.namespace):
        restart_deployment(namespace=args.namespace, name=worker, resource_limit_fraction=args.resource_limit)
