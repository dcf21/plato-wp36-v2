# Use standardised Python environment with EAS pipeline code
FROM plato/eas:v1

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/worker_bls_reference
ADD src src

# Now build the BLS reference implementation
RUN ./src/build.sh

# *** Write list of available TDAs
RUN echo '["bls_reference"]' > /plato-wp36-v2/installed_software.json

