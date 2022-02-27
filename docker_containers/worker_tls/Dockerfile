# Use standardised Python environment with EAS pipeline code
FROM plato/eas:v1

# Copy source code into the Docker container
WORKDIR /plato_eas
ADD src src

# Build TLS
RUN ./src/build.sh

# Write list of available TDAs
RUN echo '["tls"]' > /plato_eas/installed_software.json

