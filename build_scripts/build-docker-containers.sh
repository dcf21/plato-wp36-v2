#!/bin/bash

# Build all the Docker containers in which the PLATO WP36 pipeline code
# runs.

# Make sure we're running in the right directory
cd "$(dirname "$0")"
cwd=`pwd`

# Directory for storing build logs
mkdir -p ../data/datadir_local/build_logs

# Build list of all Docker containers to build
containers="../docker_containers/eas_base ../docker_containers/eas_worker_synthesis_psls_batman"

# Build each container in turn
for item in $containers
do
    cd ${cwd}/${item}
    base_name=$(basename ${item})
    docker build . --tag plato/${base_name}:v1 2>&1 | tee ../../data/datadir_local/build_logs/docker_build_${base_name}.log
    cd ${cwd}
done

# Build containers within minikube environment (which has its own Docker environment in a VM)
eval $(minikube -p minikube docker-env)

# Build each container in turn
for item in $containers
do
    cd ${cwd}/${item}
    base_name=$(basename ${item})
    docker build . --tag plato/${base_name}:v1 2>&1 | tee ../../data/datadir_local/build_logs/docker_build_minikube_${base_name}.log
    cd ${cwd}
done

