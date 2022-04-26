# Diagnostics

Some convenience scripts used to check the status of the pipeline:

* `display_job_tree.py` -- Display all of the tasks in the task database, in a nested hierarchy, indicating which subtasks were spawned by which parents.

* `mysql_shell.sh` -- Open a MySQL terminal in the task database (within the Kubernetes cluster).

* `display_message_queue.py` -- Display a list of jobs in the `eas_scheduling_attempts` table of the task database which are currently scheduled for execution.

