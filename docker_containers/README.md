# Docker containers

This directory contains the Docker containers which comprise the EAS prototype pipeline. The containers are as follows:

### `eas_base`

This contains all of the core code of the EAS pipeline infrastructure, signalling and control. A full description of its contents can be found in the `README.md` file within the container. All of the Docker containers below are derived from this parent container.

### `eas_web_interface`

This container implements a minimal web interface / control panel for the EAS pipeline, based on the Python/Flask framework. The web interface is exposed on port 5000 by default. A Kubernetes service is configured by the code `../eas_controller/kubernetes_yaml/web-interface-service.yaml` which exposes the web interface on port 30080 on the minikube virtual machine, from where the web interface is accessible on the host machine.

### `eas_worker_xxx`

These containers all provide workers which run specific science codes. There are all derived from the `eas_base` container.


