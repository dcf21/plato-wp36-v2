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
ADD configuration configuration

# Copy PLATO EAS Python modules into Docker container
ADD python_modules python_modules
ADD python_components python_components
ADD worker_diagnostics worker_diagnostics
ADD task_implementations task_implementations
ADD task_qc_implementations task_qc_implementations
ADD launch_worker launch_worker

# Build and install plato_wp36 modules
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable \
    /plato-wp36-v2/docker_containers/eas_base/python_modules/plato_wp36 --no-binary :all:
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable \
    /plato-wp36-v2/docker_containers/eas_base/python_modules/eas_psls_wrapper --no-binary :all:
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable \
    /plato-wp36-v2/docker_containers/eas_base/python_modules/eas_batman_wrapper --no-binary :all:

# Create placeholders for input and output data
RUN mkdir -p /plato-wp36-v2/data/datadir_input
RUN mkdir -p /plato-wp36-v2/data/datadir_output

# *** Write name of the Docker container into its root
RUN echo 'eas_base' > /plato-wp36-v2/container_name.txt
