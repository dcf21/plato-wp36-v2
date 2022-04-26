# Queue management

The scripts in this directory look for tasks in the task database which have not executed successfully yet, but which have no dependencies on input files which haven't been created yet. These jobs are then placed into the job queue in the message bus.

