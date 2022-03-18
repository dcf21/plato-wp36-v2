#!/bin/bash

# Install DST version 29
cd /plato-wp36-v2/docker_containers/worker_dst_v29/private_code
mkdir -p asalto29
cd asalto29 ; tar xvfz ../asalto29.tgz

# Patch Juan's Makefiles into a working state
cd /plato-wp36-v2/docker_containers/worker_dst_v29/private_code/asalto29
cp Makefile Makefile.original
patch Makefile < Makefile.asalto29.patch

# Make asalto29
make -j 4
