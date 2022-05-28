#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# stop.py

"""
Stops a Kubernetes deployment of the EAS pipeline. Currently, we fork the kubectl commandline tool rather than using the
Python API because it's massively less verbose.
"""

import argparse
import logging
import sys

from deploy import fetch_component_list, deploy_or_delete_item


def delete_all(namespace: str):
    # List of components in the order in which we create them
    components = fetch_component_list()

    # Delete components in the opposite order to which they are created
    for kubernetes_component in reversed(components):
        # Do not restart input/output persistent volumes, to avoid data loss
        if kubernetes_component.startswith("input") or kubernetes_component.startswith("output"):
            continue

        # Delete all remaining items
        deploy_or_delete_item(item_name=kubernetes_component, namespace=namespace, delete=True)


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
