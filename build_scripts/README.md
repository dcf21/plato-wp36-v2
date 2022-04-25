# Build scripts

The convenience scripts in this directory are used to build the Python 3 virtual environment in which the EAS Control scripts run, and also the Docker containers in the `docker_containers` directory which contain the code for the worker nodes.

To build the required Python virtual environment, run:

```
./create-virtual-environment.sh
```

This creates a Python virtual environment in the directory `data/datadir_local/virtualenv`. All of the Python scripts in this repository contain shebang lines which automatically

