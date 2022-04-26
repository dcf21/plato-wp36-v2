# PLATO WP36 EAS pipeline core Docker container

The Docker container in this directory contains all the core code for the workers in the PLATO WP36 EAS prototype pipeline.

All containers which run specific science codes within the pipeline should be derived from this container, which provides the communications and signalling code used to communicate with other parts of the pipeline.

The directory structure of the core container is as follows.:

* `python_modules` -- This contains the source-code for the `plato_wp36` module, which provides the Python API for interacting with the task database and retrieving/writing file products. All interaction with other parts of the EAS system should be done using this API, as the implementation details may be subject to change at any time.

* `task_type_registry.xml` -- This XML file provides a complete registry of all of the types of task that the pipeline is able to run, and the names of the Docker containers which are able to run them. This registry is used by EAS Control, when a new task is scheduled, to establish which Docker containers need to be running on the cluster in order for the task to be executed.

* `launch_worker` -- The script in this directory is the main entry point for worker nodes. It connects to the message bus and listens for work to do. It uses the name of the Docker container it is running within to establish (from the task type registry) which tasks this container is capable of running, and hence which job queues it should listen to.

* `task_implementations` -- This directory contains the Python scripts which get executed for each task that the pipeline is capable of running. When building derived containers to run new science codes, an additional script should be placed in this directory to run the new task. The scripts are deliberately quite concise, to avoid too much code duplication. The Python decorator `@task_execution.eas_pipeline_task` does the magic of running the `task_handler` function for each task in a controlled environment, with all Python logging messages transmitted to the EAS database, and with access to the arguments of the task to be performed given via a Python `Task` object. In the event of a Python traceback, this is also intercepted and transmitted to the EAS database.

* `task_qc_implementations` -- Every task in the `task_implementations` directory must also have a corresponding script in this directory which performs QC after the task has been executed. This sets a flag on each file product, and on the task as a whole, indicating whether its output is valid.

* `configuration` -- The configuration file in this directory sets global configuration options for the worker nodes.

* `worker_diagnostics` -- The shell scripts in this directory are useful when debugging a worker container by starting a bash shell within the container.
