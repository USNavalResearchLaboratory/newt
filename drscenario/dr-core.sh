#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}../" )" && pwd )"
# This needs to point to the high level NEWT directory so it can find the core tools for initialising the app.
NEWTROOT="$(dirname "$SCRIPT_DIR")"

CORE_DIR="$NEWTROOT/core-emu/"
TOOLS_DIR="$NEWTROOT/core-emu/tools"

# must be absolute path
PYTHON_SCRIPT="workflow.py"

$TOOLS_DIR/run-core.sh $CORE_DIR 9-fixed-nodes.imn $SCRIPT_DIR $PYTHON_SCRIPT