# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Copy source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/worker_synthesis_platosim
ADD build build

# Build PlatoSIM
RUN ./build/build.sh

# Link task implementations into the EAS worker distribution
RUN ln -s task_implementations/task_synthesise_platosim.py ../eas_base/task_implementations/
RUN ln -s task_qc_implementations/task_synthesise_platosim.py ../eas_base/task_qc_implementations/

# *** Write name of the Docker container into its root
RUN echo 'eas_worker_synthesis_platosim' > /plato-wp36-v2/container_name.txt
