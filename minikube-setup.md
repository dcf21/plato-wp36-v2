# minikube setup instuctions

The prerequisites to deploy the test-bench via minikube are as follows:

1. **Install minikube**

   If you need to install minikube, this can be done on a Ubuntu machine as follows. Note that you should install Docker via aptitude, not via snap, if you subsequently want to use minikube:

    ```
    apt install apt-transport-https ca-certificates curl software-properties-common
    cd
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
    add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
    apt update
    apt-cache policy docker-ce
    apt install docker-ce
    systemctl status docker

    curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add
    apt-add-repository "deb http://apt.kubernetes.io/ kubernetes-xenial main"
    apt install kubeadm
    
    wget https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
    cp minikube-linux-amd64 /usr/local/bin/minikube
    chmod 755 /usr/local/bin/minikube
    minikube version
   ```

2. **Start minikube**

    ```
    minikube start --cpus=12 --memory='9g' --mount=true
    ```

   You may wish to tweak the number of CPU cores and the amount of RAM made available to the Kubernetes cluster.

3. **Mount data directories**

   The Kubernetes cluster needs access to the directories on the host machine containing the input lightcurves and where it should write the
   output from the transit-detection codes. These two commands to mount these directories into the Kubernets cluster each need keep running, so execute them in two separate `screen` sessions:

    ```
    minikube mount --uid 999 ../data/datadir_output/:/mnt/datadir_output/
    minikube mount --uid 999 ../data/datadir_input/:/mnt/datadir_input/
    ```
   
4. **Build the Docker containers**

   The Docker containers that comprise the EAS pipeline need to be built within the minikube Docker environment (which is a virtual machine):

   ```
   cd build_scripts
   ./build-docker-containers.sh
   ```

5. **Deploy the test-bench Docker containers within Kubernetes**

    ```
    cd ../eas_controller/worker_orchestration
    ./deploy.py
    ```

6. **Watch the pods start up**

    ```
    watch kubectl get pods
    ```

   This will show a live list of the containers running within Kubernetes. It often takes a minute or two for them to
   reach the `Running` state.

7. **Initialise the databases**

   First you need to find out the port and host on which minikube is exposing the MySQL and RabbitMQ services on the host machine:

   ```
   minikube service --url mysql
   ```
   
   Then initialise the databases:

   ```
   cd eas_controller/database_initialisation
   ./init_schema.py --db_port 30036 --db_host 192.168.59.100
   ```

8. **Restart**

   To restart the test-bench, for example after changing the code:

    ```
    ./restart.sh
    ```

9. **Stop the test-bench**

   To close the test-bench down:

    ```
    ./stop.sh
    ```

10. **Stop minikube**

    To close minikube down:

     ```
     minikube stop
     minikube delete
     ```

11. **Clear out results**

    To clear out the output results and start again afresh:

     ```
     cd ../datadir_output/
     ./wipe.sh
     ```

