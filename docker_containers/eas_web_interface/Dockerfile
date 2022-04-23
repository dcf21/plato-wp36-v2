# Use standardised Python environment with EAS pipeline code
FROM plato/eas_base:v1

# Copy web interface source code into the Docker container
WORKDIR /plato-wp36-v2/docker_containers/eas_web_interface
ADD web_interface web_interface

# Move into the directory where the launch script lives
WORKDIR /plato-wp36-v2/docker_containers/eas_web_interface/web_interface

# *** Write name of the Docker container into its root
RUN echo 'eas_web_interface' > /plato-wp36-v2/container_name.txt
