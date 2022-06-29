# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)

## Directory structure

The code in this repository is arranged as follows. More information about the contents of each directory can be found in README files in each directory.

* `build_scripts` -- Convenience scripts which build the Docker containers containing the pipeline prototype.

* `docker_containers` -- Each Docker container used by the pipeline is in a separate directory. The container `eas_base` contains the core pipeline code, and all the other containers are derived from it.

* `eas_controller` -- Scripts used to deploy the prototype into a Kubernetes cluster, and to scale the deployment according to demand. This directory also contains code to initialise the database schema, the job queues, and for submitting jobs to the pipeline.

* `data` -- Storage for input files used by the prototype, for intermediate file products, and for output results.

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.