# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)

## Installation

This page provides instructions on how to install the pipeline, including how to install the required software such as Docker and Kubernetes.

Because the software runs in an isolated software environment, it is quite agnostic about the operating system running on your host machine. We have tested it using MacOS and Ubuntu Linux. We believe that it is probably impossible to run `minikube` on an M1 (ARM-based) MacBook Pro at the current time, though.

The simplest way to run the pipeline on a single laptop or desktop computer is by using `minikube`. This is a minimal Kubernetes implementation which can be run on a single machine, but which does not allow multiple machines to be connected into a cluster. It nonetheless provides a test environment which is almost identical to Kubernetes on large clusters, and one of the convenient features of Kubernetes is this ability to scale code from a single laptop to a large cluster with minimal modification.

It is also possible to run an individual worker container in a stand-alone fashion, working on test data which is built into the worker container. In this mode, the EAS interface code mimics communications with an external cluster, but in fact the communication is with a lightweight task database hosted within the container itself using `sqlite3`.

### Generic minikube installation

Instructions here provide a step-by-step guide to installing `minikube`, and the pipeline itself, on a laptop or desktop machine: [minikube-setup](minikube-setup.md).

### Stand-alone testing

Instructions here provide a step-by-step guide to running a worker node in a stand-alone fashion: [testing](testing.md).

### Deployment on the Spartan cluster (minikube)

Instuctions here provide Dominic's notes on running `minikube` on the Spartan cluster in Cambridge: [installation](minikube-spartan.md)

### Deployment on the Spartan cluster (kubernetes)

Instuctions here provide Dominic's notes on running a multi-node Kubernetes cluster on the Spartan cluster in Cambridge: [installation](k8s-spartan.md)

### Deployment on the Iris / OpenStack cluster (minikube)

Instuctions here provide Dominic's notes on running `minikube` on the Iris / OpenStack cluster in Cambridge: [installation](minikube-iris.md)

### Deployment on the Iris / OpenStack cluster (kubernetes)

Instuctions here provide Dominic's notes on running a multi-node Kubernetes cluster on the Iris / OpenStack cluster in Cambridge: [installation](k8s-iris.md)

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.