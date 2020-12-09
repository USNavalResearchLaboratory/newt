#!/bin/bash

ACT=$1
SCENE=$2
DURATION=45
POST_DURATION=10

echo "Act $ACT, Scene $SCENE"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}../" )" && pwd )"
# This needs to point to the high level NEWT directory so it can find the core tools for initialising the app.
NEWTROOT="$(dirname "$SCRIPT_DIR")"

CORE_DIR="$NEWTROOT/core-emu"
TOOLS_DIR="$NEWTROOT/core-emu/tools"

# must be absolute path
PYTHON_SCRIPT="workflow.py"

echo "Hamlet Core: running act/scene $ACT/$SCENE for $DURATION seconds"

$TOOLS_DIR/run-core2.sh $CORE_DIR 36-node-actor_cluster.imn $SCRIPT_DIR $PYTHON_SCRIPT -m core -a $ACT -s $SCENE

PYCORE_ID=$(ls /tmp | grep pycore. | grep -o '[0-9]*')

sleep $DURATION
# Stop the current running CORE emulation and eventGen
echo "Hamlet Core: Stopping CORE emulation $PYCORE_ID"
core-gui -c $PYCORE_ID

sleep $POST_DURATION

#$TOOLS_DIR/shutdown.sh

echo "END of Hamlet act/scene $ACT/$SCENE "
target="results/Collect_Act"$ACT"Scene"$SCENE""
mv /tmp/Data_Collect $target
