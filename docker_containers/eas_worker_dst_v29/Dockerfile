# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Patch Juan's Makefiles into a working state
WORKDIR /plato-wp36-v2/docker_containers/worker_dst_v29/private_code/asalto29
COPY src/Makefile.asalto29.patch Makefile.patch

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/worker_dst_v29/
ADD build build

# Now build the transit-detection code
RUN ./build/build.sh

# Link task implementations into the EAS worker distribution
RUN ln -s task_implementations/task_transit_search_dst_v29.py ../eas_base/task_implementations/
RUN ln -s task_qc_implementations/task_transit_search_dst_v29.py ../eas_base/task_qc_implementations/

# *** Write name of the Docker container into its root
RUN echo 'eas_worker_dst_v29' > /plato-wp36-v2/container_name.txt
