#!../../data/datadir_local/virtualenv/bin/python3
# -*- coding: utf-8 -*-
# deploy.py

"""
Creates a deployment of the test-bench using AppsV1Api.
"""

import os
import logging
import sys
import yaml
from kubernetes import client, config


def deploy_all():
    components = ["input-pv", "input-pvc", "output-pv", "output-pvc", "mysql-pv-minikube", "mysql-pvc-minikube",
                  "mysql-app", "mysql-service", "rabbitmq-controller", "rabbitmq-service"]
    # "eas-debugging"

    for item in components:
        deploy_item(name=item)


def deploy_item(name):
    config.load_kube_config()

    json_filename = os.path.join(os.path.dirname(__file__), "../kubernetes_yaml", "{}.yaml".format(name))

    os.system("kubectl apply -f {}".format(json_filename))


# If we're called as a script, deploy straight away
if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        stream=sys.stdout,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S')
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    deploy_all()
