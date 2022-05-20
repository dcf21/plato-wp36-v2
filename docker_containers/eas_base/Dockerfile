# This Dockerfile creates a generic Docker image containing the WP36 EAS pipeline,
# with various useful libraries installed. The containers which run the specific
# science codes which make up the pipeline should be derived from this base
# container.

# Use a Ubuntu base image
FROM ubuntu:latest

# Install various useful Ubuntu packages
RUN apt-get update
RUN apt-get install -y apt-utils dialog git vim net-tools wget rsync \
                       python3 python3-dev python3-virtualenv python3-mysqldb \
                       mysql-client libmysqlclient-dev make gcc g++ gfortran \
                       libcfitsio-dev libgsl-dev sqlite3 \
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
    python_modules/plato_wp36 --no-binary :all:

# Create placeholders for input and output data
RUN mkdir -p /plato-wp36-v2/data/datadir_input
RUN mkdir -p /plato-wp36-v2/data/datadir_output

# Move into the directory where the launch script lives
WORKDIR /plato-wp36-v2/docker_containers/eas_base/launch_worker
