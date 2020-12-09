#!/bin/bash
# THE $PYTHON_FILE_NAME is the full path that needs to be defined in the parent script to state the executable to use
# start off a ipython server

echo "Running python class in directory ${PWD##*/}"
echo "called with $PYTHON_FILE_NAME $*"

python $1 $*


