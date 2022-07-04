# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)

## Implementing new pipeline modules

This page describes the process of implementing new pipeline modules.

The following infrastructure needs to be provided to implement new pipeline tasks:


1. The XML file **`task_type_registry.xml`** within the `eas_base` container serves as a canonical reference for all of the tasks that the pipeline knows how to perform. It needs to be updated to include an entry for the new task, which includes the name of the task, the name of the container it runs in, and the amount of system resources (CPU, RAM, GPU, etc) that it requires.

2. A **Docker container** to run the task. It is possible for a single container to implement multiple tasks, but this is only a likely to be a good idea if the tasks have very similar software dependencies, and are being implemented and maintained by the same person.

3. A Python script in the **task_implementations** directory of your Docker container, which provides the entry point for your new task.

4. A Python script in the **task_qc_implementations** directory of your Docker container, which provides the entry point for performing quality control on the output of your task and deciding whether it ran successfully.

The following sections describe each of these steps in more detail:

### 1. Registering the name of your new module

You need to add some new entries in the XML file `docker_containers/eas_base/task_type_registry.xml` to define your new task.

Adding an entry to define your new task is straightforward: you simply need to define the name of the task, and the name of the Docker container that it runs within. For example:

```
<task>
    <name>transit_search_tls</name>
    <container>eas_worker_tls</container>
</task>
```

Additionally, if you are creating a new Docker container to run your task, you need to create an entry for this as well. For example:

```
<container>
    <name>eas_worker_tls</name>
    <resourceRequirements>
        <cpu>20</cpu>
        <gpu>0</gpu>
        <memory_gb>16</memory_gb>
    </resourceRequirements>
</container>
```

The resource requirements section of this structure acts as both a request and also a limit. Kubernetes will not run your container unless it is able to give your container exclusive access to all the resources you request. It will also limit your container to use no more than the resources you have requested.

It should be noted that the `eas_base` Docker container lives in a git repository that only the Cambridge group have write access to. For testing purposes, you can of course edit this file locally on your own machine. However, to propagate these settings to other users, you will need to get the Cambridge group to insert the edit the file in the public respository.

### 2. Creating a new Docker container

Now you need to start building a custom Docker container to provide the correct software environment to run your module.

#### The base container

This Docker container should be derived from the `plato/eas_base:v1` base container, which contains the core pipeline code that your worker will use to communicate with other parts of the pipeline. This means that your `Dockerfile` needs to start with the lines:

```
# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1
```

... which makes sure your container includes the core pipeline code.

After this, your `Dockerfile` contains a list of the shell commands that you need to run (as root) to install all the software your module needs. You can find several examples of how to do this in the directory `docker_containers` in this repository.

#### Software dependencies

If your container needs some Ubuntu packages, you would install them via:

```
RUN apt install <my_package>
```

If you need to install any additional Python packages, you can install them into the Python virtual environment used by the pipeline as follows:


```
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install <some_package>
```

You may also want to provide some custom Python modules of your own, to provide a wrapper to any external software you need to call. In the demonstation containers in this repository, I always place such Python modules in a directory called `python_modules`, and then install them using a line in the Dockerfile along the lines of:

```
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable python_modules/eas_tls_wrapper --no-binary :all:
```

#### Installing the task implementations

Your Docker container will need to contain three directories, `task_implementations`, `task_qc_implementations`, and `test_task_configs`, which provide the main Python entry points for executing your tasks, and some test configurations for your module.

Your `Dockerfile` will need to explicitly copy these directories into your Docker container:

```
ADD task_implementations task_implementations
ADD task_qc_implementations task_qc_implementations
ADD test_task_configs test_task_configs
```

#### Setting the right working directory

Finally, at the end of your Dockerfile, you **must** make sure that you working directory of your worker is set to the directory containing the scripts used to launch the pipeline:

```
# Move into the directory where the launch script lives
WORKDIR /plato-wp36-v2/docker_containers/eas_base/launch_worker

```

### 3. Writing a task implementation

Each pipeline task is implemented by a Python script in the directory `task_implementations`, which needs to have the special filename `task_<task_name>.py`. The implementation of the `null` pipeline task provides a good initial template to adapt to start writing a new task: `docker_containers/eas_base/task_implementations/task_null.py`.

The main body of the task implementation goes in the function `task_handler`, which is wrapped by a Python decorator line:

```
@task_execution.eas_pipeline_task
```

This one-line Python decorator sets up all of the infrastucture required for your pipeline module to interact with the rest of the pipeline. Amongst other things, it:

* Looks up all the input settings for the task, and passes your task handler a Python object `execution_attempt` which is an instance of the class `task_database.TaskExecutionAttempt` and contains all these settings.
* Ensures that any logging messages your module produces are automatically recorded in the task database.
* Sets up a background process which sends heartbeat messages to the task database every 60 seconds to confirm your task is still running. In the event that your task terminates unexpected, the EAS Controller is made aware of this when the heartbeat messages stop.

#### Accessing file inputs

The input files required by a task should be accessed by calling the function `task_db.task_open_file_input`. This takes three arguments:

|Argument  |Type|Description                                                                                                                                |
|----------|----|-------------------------------------------------------------------------------------------------------------------------------------------|
|task      |Task|An instance of the `Task` class defining the task that is being run. In most cases you will pass the value `execution_attempt.task_object`.|
|tmp_dir   |str |The path to a working directory where a copy of the input file should be placed once it is extracted from the task database.               |
|input_name|str |The semantic name of the input to be fetched (the dictionary key used in the `inputs` section of the JSON file calling the task).          |

This function call returns a list of two outputs: the full filename of the input file, in `tmp_dir`, and a dictionary of metadata associated with the input file.

It is the user's responsibility to delete the contents of `tmp_dir` once the input file is finished with. You may want to use the helper class `temporary_directory.TemporaryDirectory()`, which creates a randomly named temporary directory for the duration of a Python `with` block, and automatically deletes it at the end of the block.

#### Interpretting file inputs

Where possible, all intermediate file products within the pipeline should be read from disk, and written to disk, using helper classes within the `plato_wp36` module. This ensures that all pipeline tasks assume they are stored on disk in a standard, consistent format.

Currently, only `Lightcurve` objects have a Python class to represent them and read/write them to/from disk.

As and when the PDC has defined data models for other intermediate file products, we will need to create similar classes to represent them.

#### Writing output files

To register an output file product into the task database, you should call the function `task_db.execution_attempt_register_output`, which takes five arguments:

|Argument         |Type                |Description                                                                                                                           |
|-----------------|--------------------|--------------------------------------------------------------------------------------------------------------------------------------|
|execution_attempt|TaskExecutionAttempt|The object `execution_attempt` that was passed to your `task_handler` function.                                                       |
|output_name      |str                 |The semantic name of the output to be registered (the dictionary key used in the `outputs` section of the JSON file calling the task).|
|file_path        |str                 |The full path to the output file to be registered.                                                                                    |
|preserve         |bool                |Boolean flag indicating whether the file at `file_path` should be preseved, or deleted, once it is stored in the database.            |
|file_metadata    |dict                |A dictionary of metadata to associate with the file product.                                                                          |


#### Logging messages

Your task implementation should use Python's built-in `logging` module to produce logging output. Specifically, three methods are available:

|Method           |Description                                                                                   |
|-----------------|----------------------------------------------------------------------------------------------|
|logging.info()   |Emit a timestamped status update.                                                             |
|logging.warning()|Emit a timestamped warning message.                                                           |
|logging.error()  |Emit a timestamped error, indicating a problem that the pipeline operator needs to know about.|


Log messages produced by these function calls are all logged in the task database, and made accessible through the pipeline's web interface.

### 4. Writing a quality-control script for your task

In addition to the task implementation described in the previous section, you also need to provide a second Python script which performs quality-control checks on the output of your task. For some tasks, this might (initially, at least) just be a minimal script which automatically marks the task as having passed QC.

These QC checks are performed by a separate script to the main task implementation, because these checks should always happen, even if for some reason your main task implementation crashed (or produced a Python traceback) and exited unexpectedly.

The structure of the QC script is identical to your main task implementation, but it lives in the directory `task_qc_implementations`.

The QC script needs to do two things:

* It needs to check the output files, and set the `passed_qc` flag on those that are OK.
* It needs to set the `all_products_passed_qc` on the task execution attempt, assuming the task has run successfully.

If the QC script does not do these things, then the task will be marked as a failure in the task database, and any subsequent tasks which rely on the outputs of the task will not be executed.

A minimal script to unconditionally mark the task outputs as OK would look like:

```
for output_file in execution_attempt.output_files.values():
    task_db.file_version_update(product_version_id=output_file.product_version_id,
                                passed_qc=True)

task_db.execution_attempt_update(attempt_id=execution_attempt.attempt_id,
                                 all_products_passed_qc=True)

```

### 5. Writing some tests for your task

In the directory `test_task_configs`, you should provide some test configurations that can be used to verify that your pipeline module works. For information about how to run such tests, see [this page](testing.md).

Each test if defined by a configuration file in INI format. The fields which you can set in these configuration files have the same names as the field you would set in a [JSON file](task_chains.md) when specifying a task chain that you wanted to run in a cluster environment.

Within the [inputs] and [outputs] sections of these files, you can specify the file paths, within the Docker container, for any input data files that need to be passed to the pipeline task, and for any output files that it will create.

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.
