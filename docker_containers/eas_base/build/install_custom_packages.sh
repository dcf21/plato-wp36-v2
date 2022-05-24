#!/bin/bash

cd /plato-wp36-v2/docker_containers/eas_base/
/plato-wp36-v2/data/datadir_local/virtualenv/bin/pip install --editable python_modules/plato_wp36 --no-binary :all:
