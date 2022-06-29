# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)
* [<< Pipeline installation](install.md)

## Installing the EAS pipeline via minikube

The steps to deploy the EAS pipeline via `minikube` are described below. These instructions cover both `macOS` and Ubuntu Linux, and can probably be easily adapted for use on any other Linux distribution.

These steps are supplemented by [other installation pages](install.md) containing Dominic's notes on installing the pipeline on specific machines.

### 1. Install minikube

If you need to install minikube, this can be done as follows:

#### Ubuntu Linux

The shell commands below install Docker, kubeadm, and minikube. Note that you must install Docker via the `docker-ce` aptitude package. Don't install Docker via `snap` if you subsequently want to use minikube - you'll run into permissions issues (in Ubuntu 20.04 / 22.04, as of June 2022).

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

# Check installation succeeded
minikube version
```

To finish the installation:

* Ensure that your user account is added to the `docker` group, otherwise it won't be able to deploy Docker containers).
* Ensure that `minikube` is accessible within your `$PATH` environment variable (you may need to explicitly add `/usr/local/bin` to your `PATH`).

#### macOS

You need to install Docker Desktop and minikube as described on the Docker website.

### 2. Install required libraries

The EAS control software is going to run on the host server, not within the Kubernetes environment. This means that various libraries are needed on the host server:

#### Ubuntu Linux

```
sudo apt install build-essential python3-virtualenv python3-dev sqlite3 libmysqlclient-dev mysql-client
```

Make sure your system `locale` is set to something sensible - on a clean Ubuntu Server installation it isn't!


```
# Check locale settings
locale
```

The important part is that whatever locale you use should have a `UTF-8` suffix. Without this, Python will spew incomprehensible errors whenever you try to install packages with accented characters in their descriptions.

```
# Update locale settings to use UTF-8
sudo update-locale LANG=en_GB.UTF-8
```

You will need to open a new shell terminal to reflect the change of locale.

### 3. Start minikube

You're now ready to fire up a clean new Kubernetes cluster. On a 12-core machine with 32 GB of RAM, you might choose these settings:

```
minikube start --cpus=12 --memory='20g'
```

Under macOS, it is essential that you also specify:

```
--driver=virtualbox
```

By default `minikube` will use the `docker` driver, but under macOS this makes it impossible to access services from the host machine. This is a killer, because it means EAS Control can't access the database or job queue. Using the `virtualbox` driver works around this issue.

The amount of CPU and RAM you assign to the cluster really matter. If you're using the `virtualbox` driver, the memory you allocate to minikube will cease to be available on your host machine, so don't allocate too much. However, your Kubernetes environment will need at least 4-8 GB if you want to synthesise two-year lightcurves at 25-second cadence.


### 4. Mount data directories

It is important to realise that `minikube` runs in its own virtual machine (or Docker container, depending on your settings), with its own filing system which is entirely isolated from your host machine. Even if the Docker containers you run within the Kubernetes are configured to store intermediate file products and database files on "persistent storage" - and the EAS control software automatically configures them to do so - this "persistent storage" only exists within `minikube`'s virtual machine.

If you actually want your intermediate file products and databases to be persistent when you shut down `minikube` - and to be easily accessible on your host machine - you need to tell minikube to store these persistent volumes on the host machine, and not on disks in the VM.

To achieve this, you need to run two commands to mount directories from your host machine into the minikube VM. These commands each need keep running, so execute them in two separate `screen` sessions:

```
minikube mount --uid 999 data/datadir_output/:/mnt/datadir_output/
minikube mount --uid 999 data/datadir_input/:/mnt/datadir_input/
```

### 5. Create a Python virtual environment

You're now ready to build a Python virtual environment on your host machine in which to run all the EAS Control scripts:

```
cd build_scripts
./create-virtual-environment.sh
```

The resulting Python environment is built in `data/datadir_local/virtualenv`. All the EAS Control Python scripts include shebang lines which automatically use this virtual environment.

### 6. Unpack third-party vendor code required by the web interface

The EAS pipeline web interface requires several standard Javascript libraries. A configuration is provided to download and install them via the `bower` package-management system, but since bower depends on `node-js` (widely used by web developers but not so much by astronomers), I also include a simple tarball of all the required files:

```
cd docker_containers/eas_web_interface/web_interface/static
tar xvfz vendor_code.tar.gz
```

### 7. Build the Docker containers

The Docker containers that comprise the EAS pipeline need to be built within the minikube Docker environment (which is a virtual machine):

```
cd build_scripts
./build-docker-containers.py --target minikube
```

This Python script can also be used to build the Docker containers within the local Docker environment on your host machine, if you wish to run them in stand-alone mode or push them to an image repository. To do this, specify the `--target local` option.

### 8. Deploy the EAS Docker containers within Kubernetes

The commands below launch the core infrastructure (database and job queue) for the EAS pipeline, but doesn't start any worker nodes yet.

```
cd ../eas_controller/worker_orchestration
./deploy.py
```

We don't start any workers just yet, because they can't operate until the task database is up and running...

### 9. Watch the pods start up

```
watch kubectl get pods -n=plato
```

This will show a live list of the containers running within Kubernetes. It often takes a minute or two for them to reach the `Running` state.

### 10. Initialise the databases

Before you can connect to the database, you need to find out the port and host on which `minikube` is exposing the MySQL and RabbitMQ services on the host machine. There is a convenience function for doing this as follows:

```
minikube service --url mysql -n=plato
minikube service --url rabbitmq-service -n=plato
```

Once you know the IP address and port number for each service, you can initialise the databases using commands like this:

```
cd eas_controller/database_initialisation
./init_schema.py --db_port 30036 --db_host 192.168.49.2
./init_queues.py --mq_port 30672 --mq_host 192.168.49.2
```

These two Python scripts perform various tasks all at once. They connect to the database and message queue and set up all the empty database tables (i.e. the schema). They also import the contents of the task-type registry - the list of all the types of task the pipeline can run - from an XML file in the `eas_base` Docker image into the database. This becomes the canonical record of all the types of task the pipeline can run. Finally, they store the IP address and port number for each service in configuration files in `data/datadir_local` so that they are remembered for all future calls to the EAS Control Python scripts. As a result, you never again need to specify this information.

### 11. Port-forward the web interface

If you want to be able to access the web interface on machine other than the one running `minikube`, you need to open a port on the host machine to expose the web interface.

If you don't plan to access the web interface remotely, you can skip this step.

You need to set up a port-forward as follows, so that an external port on your host machine (in this example, 8080) is bound to the Kubernetes web interface service. The command below does not return, so you probably want to run it in a `screen` session:

```
kubectl port-forward -n=plato service/eas-web-interface-service 8080:5000  --address='0.0.0.0'
```

### 12. Start some worker nodes

Now that the database has been initialised, it's possible to start some workers:

```
cd ../eas_controller/worker_orchestration
./deploy.py --worker eas-worker-base
```

## Restarting the pipeline


To restart the prototype, for example after changing the code:

```
cd ../eas_controller/worker_orchestration
./restart_workers.sh
```

## Shutting the pipeline down

### 1. Stop the prototype

To close the EAS pipeline down:

```
 cd eas_controller/worker_orchestration
./stop.py
```

This stops all the running containers and services, but does not delete the persistent storage volumes.

### 2. Stop minikube

To close minikube down:

```
minikube stop
```

### 3. Delete minikube

If you wish to totally destroy the minikube VM, in preparation for changing your minikube configuration:

```
minikube delete
```

### 4. Clear out intermediate file products

To clear out the archive of intermediate file products and start again afresh:

```
cd data/datadir_output/
./wipe.sh
```
