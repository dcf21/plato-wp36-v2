# This Dockerfile creates a generic Docker image containing the WP36 EAS pipeline,
# with various useful libraries installed. The containers which run the specific
# science codes which make up the pipeline should be derived from this base
# container.

# Use a Ubuntu base image
FROM ubuntu:20.04

# Install various useful Ubuntu packages
RUN apt-get update
RUN apt-get install -y apt-utils dialog file git vim net-tools wget rsync \
                       python3 python3-dev python3-virtualenv python3-mysqldb \
                       mysql-client libmysqlclient-dev make gcc g++ gfortran \
                       libcfitsio-dev libgsl-dev sqlite3 \
                       ; apt-get clean

# Install Python requirements
WORKDIR /plato-wp36-v2/docker_containers/eas_base/
ADD build build
ADD requirements.txt requirements.txt

# We install all Python dependencies into a virtual environment
RUN /plato-wp36-v2/docker_containers/eas_base/build/create_virtual_environment.sh
RUN /plato-wp36-v2/docker_containers/eas_base/build/install_python_dependencies.sh

# Copy configuration into container
ADD configuration configuration

# Copy PLATO EAS Python modules and other core code into Docker container
ADD python_modules python_modules
ADD python_components python_components
ADD worker_diagnostics worker_diagnostics
ADD launch_worker launch_worker
ADD task_type_registry.xml task_type_registry.xml

# Copy task implementations for EAS core tasks
ADD task_implementations task_implementations
ADD task_qc_implementations task_qc_implementations
ADD test_task_configs test_task_configs

# Build and install plato_wp36 modules
RUN /plato-wp36-v2/docker_containers/eas_base/build/install_custom_packages.sh

# Create placeholders for input and output data
RUN mkdir -p /plato-wp36-v2/data/datadir_input
RUN mkdir -p /plato-wp36-v2/data/datadir_output

# Move into the directory where the launch script lives
WORKDIR /plato-wp36-v2/docker_containers/eas_base/launch_worker
