#!/bin/bash

# Install DST version 29
cd /plato_eas/docker_containers/private_code
mkdir -p asalto29
cd asalto29 ; tar xvfz ../asalto29.tgz

# Patch Juan's Makefiles into a working state
cd /plato_eas/docker_containers/private_code/asalto29
cp Makefile Makefile.original
patch Makefile < ../../testbed/tda_codes/dst_v29/Makefile.asalto29.patch

# Make asalto29
make -j 4

# Write list of available TDAs
echo '["dst_v29"]' > /plato_eas/docker_containers/tda_list.json
