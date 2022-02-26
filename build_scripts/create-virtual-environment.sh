#!/bin/bash

# Build a Python virtual environment containing all the dependencies for
# running the PLATO WP36 pipeline code.

# Make sure we're running in the right directory
cd "$(dirname "$0")"
cwd=`pwd`

# Create virtual environment
datadir=${cwd}/../data/datadir_local
venv_dir=${datadir}/virtualenv
rm -Rf ${venv_dir}
virtualenv -p python3 ${venv_dir}

# Install required python libraries
${venv_dir}/bin/pip install numpy
${venv_dir}/bin/pip install -r ${cwd}/../docker_containers/eas_base/requirements.txt

