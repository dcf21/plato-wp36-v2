# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)

## EAS Control

This page describes the various scripts that are available to control and monitor the pipeline's operation. All of these scripts live within the `eas_controller` directory of this repository.

#### database_initialisation/db_restore.py

This restores the task database from a backup file previously made with the `db_save.py` script.

#### database_initialisation/db_save.py

This saves the contents of the task database to a MySQL dump file on the host machine. This can be useful to create backups. It is also useful if you want to duplicate the current state of the task database on a remote cluster into a database running locally on a laptop, in order to interrogate it in detail.

#### database_initialisation/init_queues.py

Initialise a new, empty job queue. Use the `--queue_implementation` command-line argument to specify whether the job queue should be implemented via SQL transactions, or as a RabbitMQ message bus. The settings are saved into a configuration file in `data/datadir_local`, and so all future calls to `eas_controller` will use the same connection settings.

#### database_initialisation/init_schema.py

Initialise a new, empty task database, and populate it with empty tables. Use the `--db_engine` command-line argument to specify whether the database should be created within `MySQL` or `sqlite3`. The settings are saved into a configuration file in `data/datadir_local`, and so all future calls to `eas_controller` will use the same connection settings.

#### diagnostics/display_job_tree.py

Print a text-based hierarchy diagram of the tasks in the task database.

#### diagnostics/display_message_queue.py

Print a summary of how many tasks are in the job queue.

#### diagnostics/errors_list.py

Print a list of all of the error messages which have been logged in the task database. This should include every Python traceback any task has ever produced.

#### diagnostics/pass_fail_to_csv.py

Produce a CSV table summarising all the tasks which have recorded in the database that they have either passed or failed.

#### diagnostics/progress_summary.py

Produce a table summarising how many tasks are in the task database, how many have already completed, how many have failed, and how many are still waiting to run.

#### diagnostics/timings_list.py

Produce a plain-text table summarising how long tasks have taken to run, both in wall-clock time and CPU time.

#### diagnostics/timings_to_csv.py

Produce a CSV table summarising how long tasks have taken to run, both in wall-clock time and CPU time.

#### job_submission/submit.py

Request that the pipeline run an execution chain. The excecution chain should be defined by a [JSON file](task_chains.md).

#### queue_management/empty_queue.py

Empty out all of the tasks currently in the job queue. This is useful when things aren't going to plan and you want everything to stop. Now.

#### queue_management/reschedule_all_unfinished_jobs.py

Request that the pipeline have another go at running all the tasks which have failed in the past.

#### queue_management/schedule_all_waiting_tasks.py

Daemon which scans the task database for any tasks which are ready to run (i.e. they are not waiting for inputs from other tasks), and feeds them into the job queue.

#### worker_orchestration/deploy.py

If run without any command-line arguments, deploys the core instructure needed by the EAS pipeline - i.e. a database and a message queue. If one or more `--worker` arguments are supplied, then it also deploys the named types of workers.

#### worker_orchestration/restart_workers.py

Restart all worker containers, which will trigger them to pick up any new build of their Docker containers.

#### worker_orchestration/stop.py

Instruct Kubernetes to kill all the currently running containers (and not restart them).

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.
