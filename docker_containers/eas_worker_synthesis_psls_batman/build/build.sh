#!/bin/bash

# Make sure we're in the directory where this script lives
cd "$(dirname "$0")"
cwd=`pwd`

# Install PSLS and Batman
/plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install batman-package psls

# Fetch the required datafiles
./dataFetch.py

