#!/bin/bash

# For the moment (May 2022), tls requires numpy<1.22
# This means we need to replace the eas_base virtual environment with one based on an old numpy version
/plato-wp36-v2/docker_containers/eas_base/build/create_virtual_environment.sh

# Install the Transit Least Squares code via GitHub
# (doesn't work as of May 2022)
# /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install numpy==1.21

# cd /plato-wp36-v2/data/datadir_local
# git clone https://github.com/hippke/tls.git
# cd tls
# /plato-wp36-v2/data/datadir_local/virtualenv/bin/python3 setup.py install

# Install the Transit Least Squares code via PyPi
/plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install transitleastsquares

# Install the EAS core dependencies in the same virtual environment as TLS
/plato-wp36-v2/docker_containers/eas_base/build/install_python_dependencies.sh
/plato-wp36-v2/docker_containers/eas_base/build/install_custom_packages.sh

