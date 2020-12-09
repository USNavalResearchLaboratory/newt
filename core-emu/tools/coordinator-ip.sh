#!/bin/bash
# Gets the IP address of the Coordinator on the ctrl net for a running emulation

pyname=`ls /tmp | grep py. | tr -d ' '`

coordinator=/tmp/$pyname/coordinator

coordinator_ip=`vcmd -c $coordinator -- ifconfig ctrl0 | grep 'inet addr' | sed -e 's/inet addr://g' | awk '{ print $1 }'`

echo "Coordinator IP: $coordinator_ip"
