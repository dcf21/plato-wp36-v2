# Python components

The scripts in this directory are automatically run by worker nodes to perform maintenance tasks:

* `heartbeat_process.py` -- This Python script is run in the background whenever a new task is executed. It wakes up once a minute and checks whether the task is still running. If so, it updates the task database with a "heartbeat" message to indicate that the task is alive and well. This allows the EAS Controller to distinguish between long-running processes that are still executing, and those which have executed prematurely and should be re-run.

