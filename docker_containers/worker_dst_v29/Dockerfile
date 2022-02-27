# Use standardised Python environment with EAS pipeline code
FROM plato/eas:v1

# Copy source code into the Docker container
WORKDIR /plato_eas
ADD src src

# Patch Juan's Makefiles into a working state
WORKDIR /plato_eas/private_code/asalto29
COPY dst_v29/Makefile.asalto29.patch Makefile.patch

# Now build the transit-detection code in turn
RUN ./build.sh

# *** Write list of available TDAs
RUN echo '["dst_v29"]' > /plato_eas/installed_software.json

