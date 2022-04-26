# EAS Controller

The scripts in this directory are designed to be run outside of the Kubernetes cluster, to externally manage it. The tasks it performs include:

* Deploying the EAS pipeline containers and services into a Kubernetes environment.

* Scaling the deployment based on demand, including changing the numbers of different types of worker nodes based on the types of jobs currently queued for execution.

* Keeping track of which tasks in the task database are ready to be executed - i.e. all of the input file products they depend on have been created and have passed QC checks.

* Submitting new jobs to the pipeline.

* Commandline tools to provide data on the current state of the pipeline, such as what jobs as running and which are still awaiting required inputs.

The directory structure is as follows:

* `kubernetes_yaml` -- Contains all of the YAML files describing the components of an EAS pipeline Kubernetes deployment.

* `worker_orchestration` -- Scripts to automatically deploy the pipeline to a Kubernetes cluster, and to restart the worker nodes or web interface.

* `database_initialisation` -- Scripts to initialise the schema of the task database. This should be executed after deploying the pipeline onto the Kubernetes cluster (since the SQL database needs to be running), but before trying to submit any work to the pipeline.

* `job_submission` -- A script to schedule a job for execution on the pipeline. The job should be described by a JSON file.

* `queue_management` -- Scripts which check for tasks in the database which are ready to be executed, and adds them to the job queue within the message bus.

* `diagnostics` -- Scripts to help figure out why Kubernetes isn't doing what it ought to...
