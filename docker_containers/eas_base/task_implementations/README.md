# Task implementations

This directory contains the Python scripts which get executed for each task that the pipeline is capable of running.

When building derived containers to run new science codes, an additional script should be placed in this directory to run the new task. The scripts are deliberately quite concise, to avoid too much code duplication. The Python decorator `@task_execution.eas_pipeline_task` does the magic of running the `task_handler` function for each task in a controlled environment, with all Python logging messages transmitted to the EAS database, and with access to the arguments of the task to be performed given via a Python `Task` object. In the event of a Python traceback, this is also intercepted and transmitted to the EAS database.

