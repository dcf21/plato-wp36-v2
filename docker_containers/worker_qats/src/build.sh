#!/bin/bash

# Download and install QATS code
cd /plato-wp36-v2/data/datadir_local
mkdir qats
cd qats
wget https://faculty.washington.edu/agol/QATS/qats.tgz
tar xvfz qats.tgz
cd qats
make
