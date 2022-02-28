# This Dockerfile creates a generic Docker image containing the WP36 algorithm
# test-bench code, and with various useful libraries installed. From this image
# are derived various containers which run specific codes.

# Use a Ubuntu base image
FROM ubuntu:latest

# Install various useful Ubuntu packages
RUN apt-get update
RUN apt-get install -y apt-utils dialog git vim net-tools wget rsync \
                       python3 python3-dev python3-virtualenv python3-mysqldb \
                       mysql-client libmysqlclient-dev make gcc g++ gfortran \
                       libcfitsio-dev libgsl-dev \
                       ; apt-get clean

# Install Python requirements
WORKDIR /plato-wp36-v2/docker_containers/eas_base/
ADD requirements.txt requirements.txt

# We install all Python dependencies into a virtual environment
RUN mkdir -p /plato-wp36-v2/data/datadir_local
RUN virtualenv -p python3 /plato-wp36-v2/data/datadir_local/virtualenv
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install numpy  # Required by batman installer
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install -r requirements.txt

# Copy configuration into container
ADD configuration_local configuration_local

# Copy PLATO EAS Python modules into Docker container
ADD python_modules python_modules

# Build and install plato_wp36 modules
WORKDIR /plato-wp36-v2/docker_containers/eas_base/python_modules/plato_wp36/
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/python3 setup.py develop
WORKDIR /plato-wp36-v2/docker_containers/eas_base/python_modules/eas_psls_wrapper/
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/python3 setup.py develop
WORKDIR /plato-wp36-v2/docker_containers/eas_base/python_modules/eas_batman_wrapper/
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/python3 setup.py develop
