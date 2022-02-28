#!/bin/bash

# Install the Transit Least Squares code
cd /plato-wp36-v2/data/datadir_local
git clone https://github.com/hippke/tls.git
cd tls
/plato-wp36-v2/data/datadir_local/virtualenv/bin/python3 setup.py install

# Write list of available TDAs
echo '["tls"]' > /plato-wp36-v2/installed_software.json
