# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)
* [<< Pipeline installation](install.md)

## Notes on running multi-node Kubernetes on Iris / Openstack in Cambridge

This page documents Dominic's experience of running a multi-node Kubernetes cluster on Iris / Openstack.

Currently the Arcus web interface does not have any facility to automatically provision Kubernetes clusters, and so we need to install everything ourselves. Iris are possibly looking into making this slightly easier...

### 1. Provision the nodes

First you need to create a bunch of virtual machines to run your Kubernetes cluster on. The steps for doing this are described [here](minikube-iris.md), but don't proceed with installing minikube. You should create one master node and a bunch of worker nodes. They can have identical specifications, but you might want to call them `master`, `worker01`, `worker02`, etc. Only the master node needs to have a floating IP (i.e. a public IP that you can use to remotely log-in).

### 2. Create a persistent volume

Virtual machine provisioned through Arcus only have extremely limited local storage, and so you will need to mount an additional volume. In the *volumes* section of the Arcus interface, provision a new volume to store your intermediate file products on. Mount this volume onto the master node of the Kubernetes cluster, using the dropdown menu on the far right of the instances list (below 'Create Snapshot').

### 3. Partition and format the persistent volume

ssh into the master node. The persistent volume will probably appear as the device `/dev/sdb`, but as yet it has no partitions or filing systems on it. You will need to partition it and format it from the command-line.

First run `parted`:

```
mklabel gpt
mkpart primary ext4 2048s -1s
```

Then run `mkfs` to format the new partition:

```
mkfs.ext4 /dev/sdb1
```

Finally, mount the partition:

```
mkdir /media/kubenetes_vol
mount /dev/sdb1 /media/kubenetes_vol
```

### 4. Install the ssh key

The Kubernetes master nodes needs to have a copy of the ssh private key that it will use to connect to the worker nodes.

Create a file `/root/plato-key.pem` on the master node and copy the private key into it from the Arcus web interface.

If you're feeling paranoid, you might want to run:

```
chmod 600 /root/plato-key.pem
```

... to make sure only root can read the private network key. In practice there probably won't be any other users with access to your virtual machine.

### 5. Install Docker and kubeadm

Run these shell commands as root on both the master node and also all your worker nodes:

```
#!/bin/bash
apt update ; apt dist-upgrade -y

# Install Docker
apt install -y apt-transport-https ca-certificates curl gnupg-agent software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt update
apt install -y docker-ce docker-ce-cli containerd.io

# Install Kubernetes
apt install -y apt-transport-https curl
curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add
echo "deb https://apt.kubernetes.io/ kubernetes-xenial main" >> ~/kubernetes.list
mv ~/kubernetes.list /etc/apt/sources.list.d
apt update
apt install -y kubelet kubeadm kubectl kubernetes-cni
```

### 6. Disable swap

This is currently not necessary on Iris, but make sure that swap isn't enable on any worker nodes.

```
# Disable swap (not necessary on OpenStack)
swapoff -a
```

Edit `/etc/fstab` to remove swapfile.

### 7. Enabled bridged network traffic

Run these commands as root, on both the master node and all the worker nodes:

```
# Enable bridged network traffic
sysctl net.bridge.bridge-nf-call-iptables=1

# Change Docker cgroup driver
mkdir -p /etc/docker
cat <<EOF | sudo tee /etc/docker/daemon.json
{ "exec-opts": ["native.cgroupdriver=systemd"],
"log-driver": "json-file",
"log-opts":
{ "max-size": "100m" },
"storage-driver": "overlay2"
}
EOF

systemctl enable docker
systemctl daemon-reload
systemctl restart docker
```

### 8. Configure the master node

Run these commands as root:

```
kubeadm init --pod-network-cidr=192.168.0.0/24
export KUBECONFIG=/etc/kubernetes/admin.conf
ufw allow 6443
ufw allow 6443/tcp
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/kube-flannel.yml
kubectl apply -f https://raw.githubusercontent.com/coreos/flannel/master/Documentation/k8s-manifests/kube-flannel-rbac.yml
```

### 9. Add the worker nodes into the multi-node cluster

First, query the master node to find out the token you should use to add worker nodes:

```
kubeadm token create --print-join-command
```

Then, on each worker node in turn, run this command to connect them to the master node:

```
kubeadm join 192.168.0.17:6443 --token e5c5vy.ju731qoypo583n0m --discovery-token-ca-cert-hash sha256:75c315c4e27bf71454cc0642a4f8caf19c3f87b454e76ade0c0ab5d017b2f9f8
```

You should substitute the discovery token that the master node told you to use.

### 10. All done!

You can now submit jobs to the cluster from the master node.

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.
