# Installing the EAS pipeline via minikube

The prerequisites to deploy the EAS pipeline via minikube are as follows:

1. **Install minikube**

   If you need to install minikube, this can be done on a Ubuntu machine as follows. Under Ubuntu, you should install Docker via the `docker-ce` aptitude package. Don't be tempted to install Docker via snap if you subsequently want to use minikube, otherwise you'll run into permissions issues.

    ```
    # Install Docker
    apt install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    apt update
    apt install -y docker-ce docker-ce-cli containerd.io

    # Install kubeadm
    sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
    echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
    apt update
    apt install kubeadm

    # Install minikube
    cd /root
    wget https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
    cp minikube-linux-amd64 /usr/local/bin/minikube
    chmod 755 /usr/local/bin/minikube
    minikube version
   ```

2. **Start minikube**

    ```
    minikube start --cpus=12 --memory='20g' --mount=true
    ```

   The command-line options really matter here. The memory you allocate to minikube will cease to be available on your host machine, so don't allocate too much, but you need at least 4-8 GB if you want to synthesise two-year lightcurves at 25-second cadence.

    Under MacOS, it is essential that you specify:

   ```
   --driver=virtualbox
   ```

   By default `minikube` will use the `docker` driver under MacOS, but this makes it impossible to access services from the host machine. This is a killer, because it means EAS Control can't access the database or job queue,

3. **Mount data directories**

   If you want your intermediate file products and SQL database to be persistent when you shut down the Kubernetes cluster, they need to be stored on persistent storage. There are two components to this. Firstly the Kubernetes resource descriptors need to create persistent volumes to store the data on - which is already configured for you by the YAML files in `eas_controller/kubernetes_yaml`. However, because `minikube` runs in a virtual machine, you also need to tell minikube to store these persistent volumes on the host machine, and not on disks in the VM, which will get wiped when the VM is deleted.

    To achieve this, you need to run two commands to mount directories from your host machine into the minikube VM. These commands each need keep running, so execute them in two separate `screen` sessions:

    ```
    minikube mount --uid 999 ../data/datadir_output/:/mnt/datadir_output/
    minikube mount --uid 999 ../data/datadir_input/:/mnt/datadir_input/
    ```
   
4. **Create a Python virtual environment**

   Build a Python virtual environment in which to run all the EAS Control scripts on your host machine:
   ```
   cd build_scripts
   ./create-virtual-environment.sh
   ```
   The resulting Python environment is built in `data/datadir_local`. All of the EAS Control Python scripts include shebang lines which automatically use this virtual environment.

5. **Prepare third-party vendor code required by the web interface**

   The EAS pipeline web interface requires several standard Javascript libraries. A configuration is provided to download and install them via the bower package-management system, but since bower depends on node-js (widely used by web developers but not so much by astronomers), I also include a simple tarball of all the required files:

   ```
   cd docker_containers/eas_web_interface/web_interface/static
   tar xvfz vendor_code.tar.gz
   ```

6. **Build the Docker containers**

   The Docker containers that comprise the EAS pipeline need to be built within the minikube Docker environment (which is a virtual machine):

   ```
   cd build_scripts
   ./build-docker-containers.py --target minikube
   ```
   
   This Python script can also be used to build the Docker containers within the local Docker environment on your host machine, if you wish to push them to an image repository, by specifying the `--target local` option.

7. **Deploy the EAS Docker containers within Kubernetes**

    The commands below launch the core infrastructure for the EAS pipeline, but doesn't start any worker nodes yet.

    ```
    cd ../eas_controller/worker_orchestration
    ./deploy.py
    ```

8. **Watch the pods start up**

    ```
    watch kubectl get pods -n=plato
    ```

   This will show a live list of the containers running within Kubernetes. It often takes a minute or two for them to
   reach the `Running` state.

9. **Initialise the databases**

   Before you can connect to the database, you need to find out the port and host on which minikube is exposing the MySQL and RabbitMQ services on the host machine. There is a convenience function for doing this as follows:

   ```
   minikube service --url mysql -n=plato
   minikube service --url rabbitmq-service -n=plato
   ```
   
   Then initialise the databases using commands like this:

   ```
   cd eas_controller/database_initialisation
   ./init_schema.py --db_port 30036 --db_host 192.168.59.101
   ./init_queues.py --mq_port 30672 --mq_host 192.168.59.101
   ```

10. **Port-forward the web interface**

    This step is only required if you want to be able to access the web interface to the pipeline externally. If so, you need to set up a port-forward so that an external port on your host machine (in this example, 8080) is bound to the Kubernetes web interface service. The command below does not return, so you probably want to run it in a `screen` session:

    ```
    kubectl port-forward -n=plato service/eas-web-interface-service 8080:5000  --address='0.0.0.0'
    ```

11. **Start some worker nodes**

    Now that the database has been initialised, it's possible to start some workers:

    ```
    cd ../eas_controller/worker_orchestration
    ./deploy.py --worker eas-worker-base
    ```
   
12. **Restart**

    To restart the prototype, for example after changing the code:

     ```
     cd ../eas_controller/worker_orchestration
     ./restart_workers.sh
     ```

13. **Stop the prototype**

    To close the EAS pipeline down:

     ```
     ./stop.py
     ```
    
     This stops all of the running containers and services, but does not delete the persistent storage volumes.

14. **Stop minikube**

    To close minikube down:

     ```
     minikube stop
     ```

     If you wish to totally destroy the minikube VM, in preparation for changing your minikube configuration:    

     ```
     minikube delete
     ```

15. **Clear out results**

    To clear out the output results and start again afresh:

     ```
     cd data/datadir_output/
     ./wipe.sh
     ```

