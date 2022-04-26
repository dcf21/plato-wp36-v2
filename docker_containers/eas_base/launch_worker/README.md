# launch_worker

The Python script in this directory is the main entry point that gets executed when new workers are deployed.

It connects to the message bus and listens for work to do. It uses the name of the Docker container it is running within to establish (from the task type registry) which tasks this container is capable of running, and hence which job queues it should listen to.
