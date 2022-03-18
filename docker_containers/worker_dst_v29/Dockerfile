# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Patch Juan's Makefiles into a working state
WORKDIR /plato-wp36-v2/docker_containers/worker_dst_v29/private_code/asalto29
COPY src/Makefile.asalto29.patch Makefile.patch

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/worker_dst_v29/
ADD src src

# Now build the transit-detection code
RUN ./src/build.sh

# *** Write name of the Docker container into its root
RUN echo 'worker_dst_v29' > /plato-wp36-v2/container_name.txt
