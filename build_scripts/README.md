# Build scripts

The convenience scripts in this directory are used to build the Python 3 virtual environment in which the EAS Control scripts run, and also the Docker containers in the `docker_containers` directory which contain the code for the worker nodes.

### Build a Python virtual environment

To build the required Python virtual environment, run:

```
./create-virtual-environment.sh
```

This creates a Python virtual environment in the directory `data/datadir_local/virtualenv`. All the Python scripts in this repository contain shebang lines which automatically execute them within this virtual environment.

### Build the Docker containers

To build the Docker containers containing the cluster worker nodes, run:

```
./build-docker-containers.py
```

By default, this script builds each container twice, once in the local Docker environment on your host machine, and a second time within the virtual machine hosting your `minikube` cluster (which has its own Docker environment, note that it cannot normally see Docker images built locally on your host machine). This whole build process can take around 10 minutes in total. To save time, you can specify which environment the containers should be built within via the commandline argument:

```
./build-docker-containers.py --target [ all | local | minikube ]   # Default: all
```

Additionally, you can also specify which particular containers you want to build:

```
./build-docker-containers.py --container eas_base
```

