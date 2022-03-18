#!/bin/bash

# Install FORTRAN compiler
apt-get update ; apt-get install -y gfortran ; apt-get clean

# Install DFM's Python binding to Kovács et al. (2002)
cd /plato-wp36-v2/data/datadir_local
git clone https://github.com/dfm/python-bls.git
cd python-bls
/plato-wp36-v2/data/datadir_local/virtualenv/bin/python3 setup.py install
