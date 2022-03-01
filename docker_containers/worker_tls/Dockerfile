# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/worker_tls
ADD src src

# Build TLS
RUN ./src/build.sh

# Write list of available TDAs
RUN echo '["tls"]' > /plato-wp36-v2/installed_software.json

