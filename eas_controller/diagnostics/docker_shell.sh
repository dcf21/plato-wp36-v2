#!/bin/bash

# Open a shell terminal in the Docker image containing an installation of the
# WP36 pipeline code.

# Make sure we're running in the right directory
cd "$(dirname "$0")"
cwd=`pwd`

# Run Docker within the minikube environment (a VM), not locally on the host
eval $(minikube -p minikube docker-env)

# Launch interactive shell using Docker
cd ${cwd}/..
docker run -it plato/eas_base:v1 /bin/bash
