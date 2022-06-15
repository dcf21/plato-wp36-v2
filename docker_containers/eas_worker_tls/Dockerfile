# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Copy configuration file into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/eas_base/configuration
ADD configuration/installation_settings_tls.conf installation_settings_tls.conf

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/eas_worker_tls
ADD build build
ADD python_modules python_modules
ADD task_implementations task_implementations
ADD task_qc_implementations task_qc_implementations
ADD test_task_configs test_task_configs

# Build TLS
RUN ./build/build.sh

# Build and install wrapper Python modules
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable \
    python_modules/eas_tls_wrapper --no-binary :all:

# Link task implementations into the EAS worker distribution
WORKDIR /plato-wp36-v2/docker_containers/eas_base/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_tls/task_implementations/task_transit_search_tls.py \
    /plato-wp36-v2/docker_containers/eas_base/task_implementations/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_tls/task_qc_implementations/task_transit_search_tls.py \
    /plato-wp36-v2/docker_containers/eas_base/task_qc_implementations/

# Move into the directory where the launch script lives
WORKDIR /plato-wp36-v2/docker_containers/eas_base/launch_worker
