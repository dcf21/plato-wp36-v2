# Use standardised Python environment with EAS pipeline code
FROM plato/eas:v1

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/worker_qats
ADD src src

# Now build QATS code
RUN ./src/build.sh

# *** Write list of available TDAs
RUN echo '["qats"]' > /plato-wp36-v2/installed_software.json

