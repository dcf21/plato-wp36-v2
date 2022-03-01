#!/bin/bash
  
# Delete all the cached images that Docker accumulates.

# Make sure we're running in the right directory
cd "$(dirname "$0")"
cwd=`pwd`

# Prune the local docker environment first
docker system prune -f
docker rmi $(docker images -a -q)

# Prune docker environment within minikube environment
eval $(minikube -p minikube docker-env)
docker system prune -f
docker rmi $(docker images -a -q)

