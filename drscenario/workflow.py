__author__ = 'scmijt'

import methods
import deployment

from newt.wire.Transport import Transport
from newt.Workflow import Workflow, Node
import logging
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-m", "--mode", dest="mode", default="localhost",
                  help="Mode [default: %default], Options [localhost, core]",
                  metavar="MODE")
(options, args) = parser.parse_args()

if options.mode == "core":
    deploy = deployment.Core
else:
    deploy = deployment.Localhost

sampling_secs = 10

smean = 2.0
sdev = 0.5
rmean = 50.0
rdev = 5.0
tmean = 95.0
tdev = 2.0

# set to true to print out all sensor information too
methods.info_detail = False

logging.basicConfig(level=logging.DEBUG)

drc_workflow = Workflow("Disaster Recovery Workflow")

seismic_node = Node("Seismic_Sensor", True)  # True makes it send data i.e. the start nodes on a workflow
radiation_node = Node("Radiation_Sensor", True)
thermal_node = Node("Thermal_Sensor", True)
collector = Node("Collector")
erc = Node("ERC")
responder1 = Node("Responder1")
responder2 = Node("Responder2")
responder3 = Node("Responder3")
responder4 = Node("Responder4")

# This method returns data using a dictionary of data indicating the data set i.e. seismic data.
seismic_in = seismic_node.add_input_port(methods.def_sensor, mean=smean, dev=sdev, s_secs=sampling_secs,
                                         dataset="seismic", endpoint=deploy.input_seismic_sensor_address)
seismic_out = seismic_node.add_output_port(seismic="@DATA[seismic]", endpoint=deploy.output_seismic_sensor_address)

radiation_in = radiation_node.add_input_port(methods.def_sensor, mean=rmean, dev=rdev, s_secs=sampling_secs,
                                             dataset="rads", endpoint=deploy.input_radiation_sensor_address)
radiation_out = radiation_node.add_output_port(rads="@DATA[rads]", endpoint=deploy.output_radiation_sensor_address)

thermal_in = thermal_node.add_input_port(methods.def_sensor, mean=tmean, dev=tdev, s_secs=sampling_secs,
                                         dataset="thermal", endpoint=deploy.input_thermal_sensor_address)
thermal_out = thermal_node.add_output_port(thermal="@DATA[thermal]", endpoint=deploy.output_thermal_sensor_address)

collector_in1 = collector.add_input_port(methods.def_collect, endpoint=deploy.input1_collector_address)
collector_in2 = collector.add_input_port(methods.def_collect, endpoint=deploy.input2_collector_address)
collector_in3 = collector.add_input_port(methods.def_collect, endpoint=deploy.input3_collector_address)

collector_out1 = collector.add_output_port(mean="@DATA[new_mean]", dev="@DATA[new_dev]", dataset="seismic", endpoint=deploy.output1_collector_address)
collector_out2 = collector.add_output_port(mean="@DATA[new_mean]", dev="@DATA[new_dev]", endpoint=deploy.output2_collector_address)
collector_out3 = collector.add_output_port(mean="@DATA[new_mean]", dev="@DATA[new_dev]", endpoint=deploy.output3_collector_address)

collector_out4 = collector.add_output_port(mean="@DATA[new_mean]", endpoint=deploy.output_collector_to_erc_address)

erc_in = erc.add_input_port(methods.def_erc, endpoint=deploy.input_erc_address)
erc_out1 = erc.add_output_port(endpoint=deploy.output_erc_responder1_address)
erc_out2 = erc.add_output_port(endpoint=deploy.output_erc_responder2_address)
erc_out3 = erc.add_output_port(endpoint=deploy.output_erc_responder3_address)
erc_out4 = erc.add_output_port(endpoint=deploy.output_erc_responder4_address)

responder1_in = responder1.add_input_port(methods.def_responder1, endpoint=deploy.input_responder1_address)
responder2_in = responder2.add_input_port(methods.def_responder1, endpoint=deploy.input_responder2_address)
responder3_in = responder3.add_input_port(methods.def_responder2, endpoint=deploy.input_responder3_address)
responder4_in = responder4.add_input_port(methods.def_responder2, endpoint=deploy.input_responder4_address)

drc_workflow.add_node(seismic_node)
drc_workflow.add_node(radiation_node)
drc_workflow.add_node(thermal_node)
drc_workflow.add_node(collector)
drc_workflow.add_node(erc)
drc_workflow.add_node(responder1)
drc_workflow.add_node(responder2)
drc_workflow.add_node(responder3)
drc_workflow.add_node(responder4)

drc_workflow.add_edge(Transport.Multicast, Transport.JSON, seismic_out, collector_in1, deploy.sensor1_multicast_address)
drc_workflow.add_edge(Transport.Multicast, Transport.JSON, radiation_out, collector_in2, deploy.sensor2_multicast_address)
drc_workflow.add_edge(Transport.Multicast, Transport.JSON, thermal_out, collector_in3, deploy.sensor3_multicast_address)

#feedback connections

drc_workflow.add_edge(Transport.UDP, Transport.PICKLE, collector_out1, seismic_in)
drc_workflow.add_edge(Transport.UDP, Transport.PICKLE, collector_out2, radiation_in)
drc_workflow.add_edge(Transport.UDP, Transport.PICKLE, collector_out3, thermal_in)

drc_workflow.add_edge(Transport.UDP, Transport.PICKLE, collector_out4, erc_in)

drc_workflow.add_edge(Transport.ZMQ_TCP, Transport.JSON, erc_out1, responder1_in)
drc_workflow.add_edge(Transport.ZMQ_TCP, Transport.JSON, erc_out1, responder2_in)
drc_workflow.add_edge(Transport.Multicast, Transport.JSON, erc_out2, responder3_in, deploy.responder_multicast_address)
drc_workflow.add_edge(Transport.Multicast, Transport.JSON, erc_out2, responder4_in, deploy.responder_multicast_address)

Workflow.SIGMA_SERIALIZATION = True

prettify=True
serialized = drc_workflow.serialize(prettify)

# print "The workflow Serialised Looks Like This: " + serialized

# exit()


if options.mode == "core":
    drc_workflow.enact()
    import time
    time.sleep(1000)
else:
    try:
        print("Workflow running...")
        drc_workflow.enact()
        raw_input('Hit any key to exit the program ...\n')
    except KeyboardInterrupt:
        pass

    drc_workflow.clean_up()

    print("Workflow Finished ... ")
