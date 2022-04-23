#!../data/datadir_local/virtualenv/bin/python3

"""
Build the Docker containers in which the PLATO WP36 pipeline code runs.
"""

import argparse
import glob
import logging
import os

from typing import List

from plato_wp36 import settings


def build_containers(container_list: List[str], target: str):
    """
    Build some Docker container.

    :param container_list:
        The list of the names of the Docker containers we should build. They should be found in
        the directory <../docker_containers>.
    :param target:
        The target Docker environment to build the container into. Either 'local' or 'minikube'.
    :return:
        None
    """

    # Make sure we're working in the right directory
    cwd = os.getcwd()

    # Directory for storing build logs
    os.makedirs("../data/datadir_local/build_logs", exist_ok=True)

    # Are we building this container in the local docker environment, or inside minikube?
    environment = ""
    if target == "minikube":
        environment = "eval $(minikube -p minikube docker-env) ; "

    # Build each container in turn
    for item in container_list:
        os.chdir(item)
        container_name = os.path.split(item)[1]
        command = """
{environment} docker build . --tag plato/{container_name}:v1 2>&1 | \
tee ../../data/datadir_local/build_logs/docker_build_{container_name}.log
""".format(container_name=container_name, environment=environment)
        logging.info(command)
        os.system(command)
        os.chdir(cwd)


if __name__ == "__main__":
    # Read command-line arguments
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--target', default='all', type=str, dest='target',
                        choices=['all', 'local', 'minikube'],
                        help='Docker environment to build this container in')
    parser.add_argument('--container', default=None, type=str, dest='containers', action='append',
                        help='Docker containers to build')
    args = parser.parse_args()

    # Get path to where Docker containers live
    path_to_build_scripts = os.path.split(os.path.abspath(__file__))[0]
    os.chdir(path_to_build_scripts)
    path_to_containers = "../docker_containers"

    # Default list of all Docker containers to build
    if args.containers is None:
        containers = glob.glob(os.path.join(path_to_containers, "eas_*"))
    else:
        containers = [os.path.join(path_to_containers, item) for item in args.containers]

    # Fetch testbench settings
    settings = settings.Settings()

    # Set up logging
    log_file_path = os.path.join(settings.settings['dataPath'], 'plato_wp36.log')
    logging.basicConfig(level=logging.INFO,
                        format='[%(asctime)s] %(levelname)s:%(filename)s:%(message)s',
                        datefmt='%d/%m/%Y %H:%M:%S',
                        handlers=[
                            logging.FileHandler(log_file_path),
                            logging.StreamHandler()
                        ])
    logger = logging.getLogger(__name__)
    logger.info(__doc__.strip())

    # Make list of target Docker environments
    targets = [args.target]
    if args.target == 'all':
        targets = ['local', 'minikube']

    # List for jobs from the message queues
    for target in targets:
        build_containers(container_list=containers, target=target)
