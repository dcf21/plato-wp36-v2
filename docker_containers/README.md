# Docker containers

This directory contains the test-bench code, plus all the scripts needed to build / install various transit-detection codes. It contains Dockerfiles which copies all these files into Docker containers where each code can individually be built and run.

The directory structure is as follows:

* `testbench` -- All the code comprising the core test-bench code.

* `worker-xxx` -- Scripts for building each transit-detection code into a separate container.

