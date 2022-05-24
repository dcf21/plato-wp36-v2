#!/bin/bash

cd /plato-wp36-v2/docker_containers/eas_base/
/plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install numpy  # Required by batman installer
/plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install -r requirements.txt
