# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/eas_worker_bls_kovacs
ADD build build
ADD task_implementations task_implementations
ADD task_qc_implementations task_qc_implementations

# Now build the BLS code
RUN ./build/build.sh

# Link task implementations into the EAS worker distribution
WORKDIR /plato-wp36-v2/docker_containers/eas_base/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_bls_kovacs/task_implementations/task_transit_search_bls_kovacs.py \
    /plato-wp36-v2/docker_containers/eas_base/task_implementations/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_bls_kovacs/task_qc_implementations/task_transit_search_bls_kovacs.py \
    /plato-wp36-v2/docker_containers/eas_base/task_qc_implementations/

# *** Write name of the Docker container into its root
RUN echo 'eas_worker_bls_kovacs' > /plato-wp36-v2/container_name.txt
