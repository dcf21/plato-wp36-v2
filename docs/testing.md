# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)
* [<< Pipeline installation](install.md)

## Running the pipeline in stand-alone mode

In addition to running within a Kubernetes cluster environment, worker nodes can also be run in a stand-alone manner for testing. To do this, you need to install Docker on your computer, but you do not need to install any variety of Kubernetes, or any of the EAS Control platform.

### 1. Build the container you want to test

To build the Docker images for all of the pipeline worker nodes, within the local Docker environment on your computer, run the following command:

```
cd build_scripts
./build-docker-containers.py --target local
```

To build all of the workers will take around 10 minutes. If you want to save time by only building, for example, the TLS worker container, you can specify this on the command-line:

```
./build-docker-containers.py --target local --container eas_base --container eas_worker_tls
```

It's always a good idea to rebuild the `eas_base` container as well as the one you want to test, since all worker containers are derived from `eas_base`.

### 2. Run a test

You can now launch tests from the command-line as follows:

#### Test the eas_base container

```
# Test the null task - does nothing
docker run -it plato/eas_base:v1 ./launch_standalone.py --config ../test_task_configs/test_null.cfg

# Test the error task - should fail!
docker run -it plato/eas_base:v1 ./launch_standalone.py --config ../test_task_configs/test_error.cfg

# Test multiplying two demo LCs together
docker run -it plato/eas_base:v1 ./launch_standalone.py --config ../test_task_configs/test_multiply.cfg

# Test verifying a demo LC
docker run -it plato/eas_base:v1 ./launch_standalone.py --config ../test_task_configs/test_verify.cfg
```

#### Test LC synthesis

```
docker run -it plato/eas_worker_synthesis_psls_batman:v1 ./launch_standalone.py --config ../../eas_worker_synthesis_psls_batman/test_task_configs/test_psls.cfg
docker run -it plato/eas_worker_synthesis_psls_batman:v1 ./launch_standalone.py --config ../../eas_worker_synthesis_psls_batman/test_task_configs/test_batman.cfg
```

#### Test transit detection

```
docker run -it plato/eas_worker_tls:v1 ./launch_standalone.py --config ../../eas_worker_tls/test_task_configs/test_tls.cfg
docker run -it plato/eas_worker_qats:v1 ./launch_standalone.py --config ../../eas_worker_qats/test_task_configs/test_qats.cfg
```

### 3. Creating your own tests

Tests are defined by configuration files which live within the `test_task_configs` directory within each Docker container. These are the filenames which appear at the end of each of the commands listed above.

Whenever you implement a new pipeline task, it is good to include at least one test that can be used to check that the pipeline task runs on any new pipeline installation.

The fields which you can set in these configuration files have the same names as the field you would set in a [JSON file](task_chains.md) when specifying a task chain that you wanted to run in a cluster environment.

Within the [inputs] and [outputs] sections of these files, you can specify the file paths, within the Docker container, for any input data files that need to be passed to the pipeline task, and for any output files that it will create.

### 4. How it works

The Python script `eas_base/launch_worker/launch_standalone.py` creates a test environment which mimics the environment seen within a worker node when running in a cluster. It creates a small task database using `sqlite3` within the Docker container, and it takes the information within the configuration file defining the test, and uses that to create a task entry within this database. If the task requires input files, it creates an additional entry for a fictious previous task which supposedly created these input files.

Having done this, it marks the test task as ready to run, configures the container to use a SQL-based job queue (rather than a message bus), and then launches the identical script that is used to receive jobs when running on a cluster (the script `eas_base/launch_worker/launch_service_mode.py`).

From here on, the path followed by the test is identical to what would happen in a cluster environment, except that the container is connecting to a local `sqlite3` database rather than a remote `MySQL` database. The container picks up the task that it is supposed to run, and runs it. After completing the task, the job queue is then empty, and the worker exits.

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.
