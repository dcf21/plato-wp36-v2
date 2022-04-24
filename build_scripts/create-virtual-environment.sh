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
${venv_dir}/bin/pip install --editable \
    ${cwd}/../docker_containers/eas_base/python_modules/plato_wp36 --no-binary :all:

# Install the PSLS wrapper
${venv_dir}/bin/pip install --editable \
    ${cwd}/../docker_containers/eas_worker_synthesis_psls_batman/python_modules/eas_psls_wrapper \
    --no-binary :all:

# Install the batman wrapper
${venv_dir}/bin/pip install --editable \
    ${cwd}/../docker_containers/eas_worker_synthesis_psls_batman/python_modules/eas_batman_wrapper \
    --no-binary :all:

# Install TDA wrappers
for tda in bls_kovacs bls_reference dst_v26 dst_v29 exotrans qats tls
do
  ${venv_dir}/bin/pip install --editable \
      ${cwd}/../docker_containers/eas_worker_${tda}/python_modules/eas_${tda}_wrapper --no-binary :all:
done
