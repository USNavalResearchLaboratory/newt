Disaster Response Scenario.

A diagram outlining the full scenario is provided in the doc directory (DRScenario.png)


Implementation Status
=====================

Basic Workflow Test Scenario Sketch with Communication Exchanges for Newt:

Nodes:

1 - seismic_node: sensor that collects seismic data
2 - radiation_node: sensor that collects radiation data
3 - thermal_node: sensor that collects thermal data
4 - collector: collector that receives sensor information and sends reports to ERC
    - three input ports for receiving sensor data
    - four output ports, three for feedback into sensors and one to connect to ERC
5 - erc: emergency response center receives reports and based on content, does nothing, or sends a message to
responder1 or responder2 to deploy
6 - responder1: dummy node that prints out deploying responders 1
7 - responder2: dummy node that prints out deploying responders 2

Links:

seismic_out -> collector_in1 (Multicast, JSON)
radiation_out -> collector_in2 (Multicast, JSON)
thermal_out => collector_in3 (Multicast, JSON)

collector_out1 -> seismic_in (UDP, PICKLE)
collector_out2 -> radiation_in (UDP, PICKLE)
collector_out3 -> thermal_in (UDP, PICKLE)

collector_out4 -> erc_in (UDP, PICKLE)

erc_out1 -> responder1_in (ZMQ_TCP, JSON)
erc_out2 -> responder2_in (Multicast, JSON)

Description
===========

Three sensors use separate multicast addresses to send seismic, thermal and radiation data to a collector node.
Each uses different mean and standard deviations, but the same underlying method for generating data (simple to
swap this with separate ones, if desired).  The collector node has three separate input ports to connect these
to one internal method (could connect to separate methods also but we want to combine here). Data arrives
asynchronously and the method (def_sensor) is thread locked so the collector processes them independently.

The collector has a random variable (def_collect.big_bang in methods) that specifies when a disaster starts. Before
the disaster, it sends (using UDP) a trigger back to the sensors steering them to use a new mean and standard deviation
values. Once the disaster happens, it changes the values of mean and dev for seismic to trigger an event.  Once this
is triggered, the mean and standard deviation values for thermal and radiation are incremented as different
casual effects are triggered upon the seismic event (earthquake). These values are fed back into the sensors to
trigger further sensor inputs and the values grow through a feedback loop.

The collector sends message (using UDP) to the ERC node telling it of the current thermal value (a report).  Once
the first level is reached (thermal value 100), the ERC triggers an event to tell the first set of responders to
be deployed by sending a ZMQ message to responder1. Upon event 2 (105), the second responder (responder2) is called
and deployed by sending a multicast message to this node. Once the thermal level reaches 110, the workflow
closes all output ports and once the data filters through the workflow, the workflow finishes.

You can edit the workflow by editing workflow.py and change any of the transport protocols at any of the links. There
is a deploy.py file that contains one deployment pattern (the binding addresses for each node) for localhost. To
deploy in CORE I need to fill in the Core deployment class and all code should work without change.


To Run
======

cd drscenario
python workflow.py


To Run In CORE
==============

cd drscenario
sudo ./dr-core.sh



Dependencies
============

python 2.7
netifaces - for getting the local host address reliably
    easy_install netifaces
wmctrl - for resizing the CORE window
    sudo apt-get install wmctrl
