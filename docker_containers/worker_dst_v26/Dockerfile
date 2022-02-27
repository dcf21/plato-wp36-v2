# Use standardised Python environment with EAS pipeline code
FROM plato/eas:v1

# Copy source code into the Docker container
WORKDIR /plato_eas
ADD src src

# Patch Juan's Makefiles into a working state
WORKDIR /plato_eas/private_code/juan
COPY dst_v26/Makefile.juan.patch Makefile.patch

WORKDIR /plato_eas/private_code/asalto26.5
COPY dst_v26/Makefile.asalto26.5.patch Makefile.patch

WORKDIR /plato_eas/private_code/asalto27
COPY dst_v26/Makefile.asalto27.patch Makefile.patch

# Now build the transit-detection code
RUN ./src/build.sh

# *** Write list of available TDAs
RUN echo '["dst_v26"]' > /plato_eas/installed_software.json

