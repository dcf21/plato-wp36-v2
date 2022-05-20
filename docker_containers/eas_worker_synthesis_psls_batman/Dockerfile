# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/eas_worker_synthesis_psls_batman/
ADD build build
ADD python_modules python_modules
ADD task_implementations task_implementations
ADD task_qc_implementations task_qc_implementations

# Build and install wrapper Python modules
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable \
    python_modules/eas_psls_wrapper --no-binary :all:
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable \
    python_modules/eas_batman_wrapper --no-binary :all:

# Fetch PSLS data files
RUN ./build/build.sh

# Link task implementations into the EAS worker distribution
WORKDIR /plato-wp36-v2/docker_containers/eas_base/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_synthesis_psls_batman/task_implementations/task_synthesis_batman.py \
    /plato-wp36-v2/docker_containers/eas_base/task_implementations/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_synthesis_psls_batman/task_implementations/task_synthesis_psls.py \
    /plato-wp36-v2/docker_containers/eas_base/task_implementations/

RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_synthesis_psls_batman/task_qc_implementations/task_synthesis_batman.py \
    /plato-wp36-v2/docker_containers/eas_base/task_qc_implementations/
RUN ln -s /plato-wp36-v2/docker_containers/eas_worker_synthesis_psls_batman/task_qc_implementations/task_synthesis_psls.py \
    /plato-wp36-v2/docker_containers/eas_base/task_qc_implementations/

# Move into the directory where the launch script lives
WORKDIR /plato-wp36-v2/docker_containers/eas_base/launch_worker
