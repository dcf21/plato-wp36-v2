This directory contains API documentation for Python the `plato_wp36` interface class, auto-generated by Sphinx.

The commands used to generate this documentation were:

```
source ../../data/datadir_local/virtualenv/bin/activate
pip3 install sphinx-markdown-builder sphinx
sphinx-quickstart 
sphinx-apidoc -o source/ ../../docker_containers/eas_base/python_modules/plato_wp36/src/plato_wp36/
make html
```