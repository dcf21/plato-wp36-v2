#!/bin/bash

# Install DST version 26
cd /plato-wp36-v2/docker_containers/worker_dst_v26/private_code
mkdir -p asalto26.5
cd asalto26.5
tar xvfz ../asalto26.5.tar.gz

cd /plato-wp36-v2/docker_containers/worker_dst_v26/private_code
mkdir -p asalto27
cd asalto27
tar xvfz ../asalto27.tar.gz

cd /plato-wp36-v2/docker_containers/worker_dst_v26/private_code
mkdir -p juan
cd juan
tar xvfz ../juan.tar.gz

# Patch Juan's Makefiles into a working state
cd /plato-wp36-v2/docker_containers/worker_dst_v26/private_code/juan
cp Makefile Makefile.original
patch Makefile < Makefile.juan.patch

cd /plato-wp36-v2/docker_containers/worker_dst_v26/private_code/asalto26.5
cp Makefile Makefile.original
patch Makefile < Makefile.asalto26.5.patch

cd /plato-wp36-v2/docker_containers/worker_dst_v26/private_code/asalto27
cp Makefile Makefile.original
patch Makefile < Makefile.asalto27.patch

# Build Juan's code: libjuan
cd /plato-wp36-v2/docker_containers/worker_dst_v26/private_code/juan
make -j 4

# Build Juan's code: asalto27
cd /plato-wp36-v2/docker_containers/worker_dst_v26/private_code/asalto27
make -j 4

# Build Juan's code: asalto26.5
cd /plato-wp36-v2/docker_containers/worker_dst_v26/private_code/asalto26.5
make -j 4

# Write list of available software
echo '["dst_v26"]' > /plato-wp36-v2/installed_software.json
