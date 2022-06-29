# PLATO WP36 EAS pipeline prototype

* [<< Documentation table of contents](contents.md)
* [<< Pipeline installation](install.md)

## Notes on running minikube on Iris / Openstack in Cambridge

Running `minikube` on a virtual machine deployed on Iris/OpenStack is quite straightforward.

The most difficult part is actually using the OpenStack web interface to create a virtual machine in the first place.

The steps are as follows:

### Log into Arcus

* Log into the Arcus control panel. Select "federated login", and use your Cambridge email address and Raven password: [https://arcus.openstack.hpc.cam.ac.uk/auth/login/?next=/project/](https://arcus.openstack.hpc.cam.ac.uk/auth/login/?next=/project/)
* Select the "iris-plato" project in the top-left corner.

### First-time configuration

Steps which Dominic has already done within the "iris-plato" project, but which need to be done within a clean project:

* Create a virtual network in the *Network > Networks* panel. I called it *plato-net*. You need to select an IP range. Try 192.168.0.0/24
* Create a router to route traffic from your virtual network onto the internet in the *Network > Routers* panel. I called it *plato-router*.
* Create a security group in the *Network > Security groups* panel. I called it *default*. By default the security group should already allow ssh traffic to reach your virtual machines, but you may need to add custom rules to open other ports, for example for the web interface.
* Create an ssh key pair that you will use to connect to the virtual machine. Do this in the *Compute > Key pairs* panel of the interface. I called mine *plato-key*. Download a copy of the private key to your laptop; you will use it to log into any virtual machines you create.

### Create a virtual machine

* Open the *Compute > Instances* panel. Click on *Launch Instance* (top middle of screen).
* Select an operating system image for the VM to run, in the *Source* panel. I choose *Ubuntu-Focal-20.04-20220411*.
* Select a flavour - i.e. hardware spec - for your virtual machine. All the defaults on Iris are tiny - the largest is eight virtual cores (i.e. four physical cores, with hyperthreading). Email research computing services helpdesk and get them to create you a custom flavour with more cores.
* Make sure that all the panels below are configured with the various bits of infrastructure you created above.
* Click on *Launch Instance*, and wait for the new virtual machine to reach a state of *Running* in the status panel.
* Nearly there... but you still can't actually log into your virtual machine until you assign it an IP address. In the actions drop-down menu (far right of the screen), under *Create Snapshop*, there's a well-hidden option *Associate floating-IP*. This will assign a public IP address to your VM, which will appear in the status panel after a few seconds.

### Configure a virtual machine

If you're lucky, you should now be able to log into your VM as follows:

```
ssh -i plato-key.pem ubuntu@128.232.222.26
```

Remember to substitute the IP address of your particular VM. You need to be connected to the IoA VPN for this to work, as Iris machines are not visible to the public internet.

### Install minikube and the EAS pipeline

Now follow [the generic minikube installation instructions](minikube-setup.md).

---

## Author

This code is developed and maintained by Dominic Ford, at the Institute of Astronomy, Cambridge.
