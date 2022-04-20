#!/bin/bash

# Make sure we're in the directory where this script lives
cd "$(dirname "$0")"
cwd=`pwd`

# Fetch the required datafiles
./dataFetch.py

