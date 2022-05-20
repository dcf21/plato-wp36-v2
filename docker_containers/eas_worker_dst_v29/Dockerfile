# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Patch Juan's Makefiles into a working state
WORKDIR /plato-wp36-v2/docker_containers/eas_worker_dst_v29/private_code/asalto29
COPY src/Makefile.asalto29.patch Makefile.patch

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/eas_worker_dst_v29/
ADD build build
ADD python_modules python_modules
ADD task_implementations task_implementations
ADD task_qc_implementations task_qc_implementations

# Build the transit-detection code
RUN ./build/build.sh

# Build and install wrapper Python modules
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable \
    python_modules/eas_dst_v29_wrapper --no-binary :all:

# Link task implementations into the EAS worker distribution
WORKDIR /plato-wp36-v2/docker_containers/eas_base/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_dst_v29/task_implementations/task_transit_search_dst_v29.py \
    /plato-wp36-v2/docker_containers/eas_base/task_implementations/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_dst_v29/task_qc_implementations/task_transit_search_dst_v29.py \
    /plato-wp36-v2/docker_containers/eas_base/task_qc_implementations/

# Move into the directory where the launch script lives
WORKDIR /plato-wp36-v2/docker_containers/eas_base/launch_worker
