# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/eas_worker_synthesis_psls_batman/
ADD build build
ADD python_modules python_modules
ADD task_implementations task_implementations
ADD task_qc_implementations task_qc_implementations

# Build and install plato_wp36 modules
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable \
    python_modules/eas_psls_wrapper --no-binary :all:
RUN /plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable \
    python_modules/eas_batman_wrapper --no-binary :all:

# Link task implementations into the EAS worker distribution
RUN ln -s task_implementations/task_synthesise_batman.py ../eas_base/task_implementations/
RUN ln -s task_implementations/task_synthesise_psls.py ../eas_base/task_implementations/

RUN ln -s task_qc_implementations/task_synthesise_batman.py ../eas_base/task_qc_implementations/
RUN ln -s task_qc_implementations/task_synthesise_psls.py ../eas_base/task_qc_implementations/

# Fetch PSLS data files
RUN ./build/build.sh

# *** Write name of the Docker container into its root
RUN echo 'eas_worker_synthesis_psls_batman' > /plato-wp36-v2/container_name.txt
