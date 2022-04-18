# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/worker_bls_kovacs
ADD src src

# Now build the BLS code
RUN ./src/build.sh

# *** Write name of the Docker container into its root
RUN echo 'eas_worker_bls_kovacs' > /plato-wp36-v2/container_name.txt
