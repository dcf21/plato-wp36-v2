# Use standardised Python environment with EAS pipeline code
FROM plato/eas:v1

# Copy source code into the Docker container
WORKDIR /plato_eas
ADD src src

# Now build the BLS code
RUN ./src/build.sh

# *** Write list of available TDAs
RUN echo '["bls_kovacs"]' > /plato_eas/installed_software.json

