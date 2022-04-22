# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Patch Juan's Makefiles into a working state
WORKDIR /plato-wp36-v2/docker_containers/eas_worker_dst_v26/private_code/juan
COPY src/Makefile.juan.patch Makefile.patch

WORKDIR /plato-wp36-v2/docker_containers/eas_worker_dst_v26/private_code/asalto26.5
COPY src/Makefile.asalto26.5.patch Makefile.patch

WORKDIR /plato-wp36-v2/docker_containers/eas_worker_dst_v26/private_code/asalto27
COPY src/Makefile.asalto27.patch Makefile.patch

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/eas_worker_dst_v26/
ADD build build
ADD task_implementations task_implementations
ADD task_qc_implementations task_qc_implementations

# Now build the transit-detection code
RUN ./build/build.sh

# Link task implementations into the EAS worker distribution
WORKDIR /plato-wp36-v2/docker_containers/eas_base/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_dst_v26/task_implementations/task_transit_search_dst_v26.py \
    /plato-wp36-v2/docker_containers/eas_base/task_implementations/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_dst_v26/task_qc_implementations/task_transit_search_dst_v26.py \
    /plato-wp36-v2/docker_containers/eas_base/task_qc_implementations/

# *** Write name of the Docker container into its root
RUN echo 'eas_worker_dst_v26' > /plato-wp36-v2/container_name.txt
