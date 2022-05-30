#!/bin/bash

# Open a MySQL terminal in the Kubernetes mysql service.

# Make sure we're running in the right directory
cd "$(dirname "$0")"
cwd=`pwd`

mysql --defaults-extra-file=../../data/datadir_local/mysql_sql_login.cfg plato

