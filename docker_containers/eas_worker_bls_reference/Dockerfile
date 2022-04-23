# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/eas_worker_bls_reference
ADD build build
ADD task_implementations task_implementations
ADD task_qc_implementations task_qc_implementations

# Build the BLS reference implementation
RUN ./build/build.sh

# Build and install wrapper Python modules
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable \
    python_modules/eas_bls_reference_wrapper --no-binary :all:

# Link task implementations into the EAS worker distribution
WORKDIR /plato-wp36-v2/docker_containers/eas_base/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_bls_reference/task_implementations/task_transit_search_bls_reference.py \
    /plato-wp36-v2/docker_containers/eas_base/task_implementations/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_bls_reference/task_qc_implementations/task_transit_search_bls_reference.py \
    /plato-wp36-v2/docker_containers/eas_base/task_qc_implementations/

# Move into the directory where the launch script lives
WORKDIR /plato-wp36-v2/docker_containers/eas_base/launch_worker

# *** Write name of the Docker container into its root
RUN echo 'eas_worker_bls_reference' > /plato-wp36-v2/container_name.txt
