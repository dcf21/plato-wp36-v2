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

# Install plato_wp36 package
cd ${cwd}/../docker_containers/eas_base/python_modules/plato_wp36/
${venv_dir}/bin/python setup.py develop

# Install the PSLS wrapper
cd ${cwd}/../docker_containers/eas_base/python_modules/eas_psls_wrapper/
${venv_dir}/bin/python setup.py develop

# Install the batman wrapper
cd ${cwd}/../docker_containers/eas_base/python_modules/eas_batman_wrapper/
${venv_dir}/bin/python setup.py develop
