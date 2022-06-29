# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)

## Pipeline modules

The pipeline prototype is already a highly capable tool which can be used for testing the performance of algorithms and techniques on synthetic PLATO lightcurves.

The following tasks can be performed by the prototype, and sequenced together into "execution chains" to build more complex processes:

* Synthesising lightcurves with PSLS.
* Synthesising lightcurves with Batman.
* Injecting white noise into lightcurves.
* Importing lightcurves from external sources, including the light-curve stitching group (LCSG).
* Multiplying lightcurves together to inject transits.
* Searching for transits with a range of transit-detection codes, including: BLS, TLS, QATS.
* Lightcurve diagnostics - verifying that lightcurves contain valid data.
* QC - all tasks are automatically followed-up by a QC task to test whether the output is valid.

This page provides a comprehensive list of the tasks currently implemented within the pipeline. Click on the name of any particular task to see its full API reference.

## Current list of pipeline modules

#### Science modules

The table below lists the modules that have already been implemented into the pipeline prototype:


|Task name                   |Container                       |Description                                                                           |
|----------------------------|--------------------------------|--------------------------------------------------------------------------------------|
|binning                     |eas_base                        |Re-bin a LC onto a new, fixed, timestep                                               |
|ingest_external_lcs         |eas_base                        |Ingest LCs generated externally, including from the LCSG                              |
|multiply                    |eas_base                        |Multiply two LCs together (for transit injection)                                     |
|synthesis_batman            |eas_worker_synthesis_psls_batman|Synthesise a LC using Batman                                                          |
|synthesis_psls              |eas_worker_synthesis_psls_batman|Synthesise a LC using PSLS                                                            |
|transit_search_bls_kovacs   |eas_worker_bls_kovacs           |Search for transits using BLS (Kovacs implementation)                                 |
|transit_search_bls_reference|eas_worker_bls_reference        |Search for transits using BLS (Astropy implementation)                                |
|transit_search_qats         |eas_worker_qats                 |Search for transits using QATS ([Carter & Agol 2012](https://arxiv.org/abs/1210.5136))|
|transit_search_tls          |eas_worker_tls                  |Search for transits using TLS ([Hippke & Heller 2019](https://github.com/hippke/tls)) |
|verify                      |eas_base                        |Verify whether a LC is sampled on a fixed timestep, and output statistics.            |

#### Flow control

The following tasks are used for flow control within pipeline task chains:

|Task name              |Container|Description                                                                                                                                           |
|-----------------------|---------|------------------------------------------------------------------------------------------------------------------------------------------------------|
|execution_chain        |eas_base |Execute a sequence of tasks. The tasks may be executed sequentially or in parallel, depending on their stated input dependencies.                     |
|execution_conditional  |eas_base |Conditionally execute a sequence of tasks, based on whether a metadata condition is met. If the condition is not met, execute an alternative sequence.|
|execution_do_while_loop|eas_base |Repeatedly execute a sequence of tasks, until a metadata condition is met (for example, search for transit signals until no more are found).          |
|execution_for_loop     |eas_base |Execute a sequence of tasks repeatedly, either in a `for` loop, or in a `foreach` loop.                                                               |

#### Testing

The following tasks are used for testing purposes and are unlikely to have any real applications:

|Task name|Container|Description                                                         |
|---------|---------|--------------------------------------------------------------------|
|error    |eas_base |Throw an error (which should get logged).                           |
|null     |eas_base |Sleep for 10 seconds, and then mark the task successfully completed.|


#### Stubs for future expansion

The following tasks are currently place-holders, and are not implemented:

|Task name              |Container                    |Description                                |
|-----------------------|-----------------------------|-------------------------------------------|
|synthesis_platosim     |eas_worker_synthesis_platosim|Synthesis a LC using PlatoSim.             |
|transit_search_dst_v26 |eas_worker_dst_v26           |Search for transits using DST (version 26).|
|transit_search_dst_v29 |eas_worker_dst_v29           |Search for transits using DST (version 29).|
|transit_search_exotrans|eas_worker_exotrans          |Search for transits using ExoTrans.        |

