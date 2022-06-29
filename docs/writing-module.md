# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)

## Implementing new pipeline modules

This page describes the process of implementing new pipeline modules.

The following infrastructure needs to be provided to implement new pipeline tasks:

* A **Docker container** to run the task. It is possible for a single container to implement multiple tasks, but this is only a likely to be a good idea if the tasks have very similar software dependencies, and are being implemented and maintained by the same person.
* A Python script in the **task_implementations** directory of your Docker container, which provides the entry point for your new task.
* A Python script in the **task_qc_implementations** directory of your Docker container, which provides the entry point for performing quality control on the output of your task and deciding whether it ran successfully.

Additionally, the XML file `task_type_registry.xml` within the `eas_base` container needs to be updated to include an entry for the new task. For testing purposes, you can of course edit this file locally on your own machine. However, to propagate these settings to other users, you will need to get the Cambridge group to insert the entry, since this file is in a git repository managed by WP365, it is necessary.

In addition to registering the name of your new pipeline task and the name of the container that implements it, you also need to specify how many CPU cores is requires, how much RAM it needs, and how many GPU cards it requires. These resource values act as both a request and a limit - i.e. your Docker container will not run on a particular machine unless there are adequate resources available, but it will also not be allowed to use more than it requested.

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.
