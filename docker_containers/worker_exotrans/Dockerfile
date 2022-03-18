# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/worker_exotrans
ADD src src

# Now build the transit-detection code
RUN ./src/build.sh

# *** Write name of the Docker container into its root
RUN echo 'worker_exotrans' > /plato-wp36-v2/container_name.txt
