# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)
* [<< Pipeline installation](install.md)

## Notes on running minikube on the Spartan cluster

On a clean Spartan node (running Ubuntu Server 20.04), the following shell commands need to be run as root to set up minikube:

```
# Install Docker
apt install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
ls
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# Install kubeadm
sudo curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg
echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | sudo tee /etc/apt/sources.list.d/kubernetes.list
apt update
apt install kubeadm

# Make sure all packages are running latest versions
apt dist-upgrade

# Install minikube
cd
wget https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
cp minikube-linux-amd64 /usr/local/bin/minikube
chmod 755 /usr/local/bin/minikube

# Check that minikube works
minikube version

# Install build dependencies and fix the locale
apt install python3-virtualenv python3-dev sqlite3 libmysqlclient-dev build-essential mysql-client
update-locale LANG=en_GB.UTF-8

```

### Start minikube

You are now ready to start `minikube`. Suitable settings on a spartan node are as follows:

```
minikube start --cpus=120 --memory='240g' --mount-string "/home/dcf21/plato-wp36-v2/data/datadir_output/:/mnt/datadir_output/" --mount=true
```

This allocates 120 CPU cores and 240 GB of RAM to Kubernetes.

On the Spartan cluster, it is currently necessary to mount the persistent data directory as shown above, differently from the steps described in step 4 of [the generic minikube installation instructions](minikube-setup.md). I think this is because the `iptables` configuration on spartan blocks the port that the `minikube mount` command uses to mount the drive into the `minikube` virtual machine.

You can now follow steps 5-11 as described in [the generic minikube installation instructions](minikube-setup.md).

### Deploying workers

Given the abundance of cores and memory available on each Spartan node, you may want to deploy quite a lot of workers:

First create a deployment for each type of worker:

```
./deploy.py --worker eas-worker-synthesis-psls-batman --worker eas-worker-tls --worker eas-worker-bls-reference --worker eas-worker-qats
```

Now you can change the replication count on each type of worker to really scale up the number of workers:

```
kubectl scale --replicas=4 deployment/eas-worker-bls-reference -n=plato
kubectl scale --replicas=4 deployment/eas-worker-qats -n=plato
kubectl scale --replicas=8 deployment/eas-worker-synthesis-psls-batman -n=plato
```

... or perhaps even more than that ...

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.
