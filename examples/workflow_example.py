__author__ = 'scmijt'

from newt.wire.Transport import Transport
from newt.Workflow import Endpoint, Workflow, Node, Edge, Port

import logging

count = 0


def def_sensor_collect(transport, *args, **kwargs):
    print "Seismic Node: Collecting more sensor information... workflow looping is working :)"

    return {"Seismic": [1, 2, 4, 5, 6]}


def def_decision_method(transport, *args, **kwargs):
    ports = transport.workflow.get_my_output_ports(transport)
    feed_back = ports[0]
    notify = ports[1]

    print "(Iteration " + str(def_decision_method.count) + ") Decision node: using transport " + transport.__class__.__name__ + " Was passed: "

    for i in range(len(args)):
        print args[i]

    def_decision_method.count += 1

    if def_decision_method.count > 10:
        print "(Iteration " + str(def_decision_method.count) + ") Decision Node: Received Sensor Data And Threshold Met !!!!"
        print "(Iteration " + str(def_decision_method.count) + ") Decision Node: Setting notification to be enabled to send to Notification Node!"
        feed_back.enabled = False
        notify.enabled = True
    else:
        print "(Iteration " + str(def_decision_method.count) + ") Decision Node: Received Sensor Data But Data Threshold Not Met"
        print "(Iteration " + str(def_decision_method.count) + ") Decision Node: looping back to the Seismic Sensor Node"
        feed_back.enabled = True
        notify.enabled = False


# Initialise count
def_decision_method.count = 0  # Interesting ! python can have static counts on methods ...


def def_notification_method(transport, *args, **kwargs):
    print "Notification node: using transport " + transport.__class__.__name__ + ", I received this notification:"

    for i in range(len(args)):
        print args[i]

    for key, value in kwargs.iteritems():
        print "%s = %s" % (key, value)

logging.basicConfig(level=logging.INFO)

# set up addresses

input_seismic_address = Endpoint("localhost", 5352)
input_threshold_address = Endpoint("localhost", 5454)
input_notify_address = Endpoint("localhost", 5455)
output_seismic_address = Endpoint("localhost", 5456)
output_seismic_thresold_address = Endpoint("localhost", 5457)
output_threshold_notify_address = Endpoint("localhost", 5458)
multicast_address = Endpoint("224.1.2.3", 5459)

# Define workflow. Set up nodes, add input and output ports to nodes and connect the edges.

my_workflow = Workflow("Demo workflow")

seismic_node = Node("Seismic_Sensor")
seismic_node.initiator = True  # Mark this as a start node for the workflow even though it has a receive port.
threshold_node = Node("Threshold_detection")
notify_node = Node("Notify")

seismic_in = seismic_node.add_input_port(def_sensor_collect, None, endpoint=input_seismic_address)
seismic_out = seismic_node.add_output_port("@DATA[Seismic]", endpoint=output_seismic_address)

threshold_in = threshold_node.add_input_port(def_decision_method, endpoint=input_threshold_address)
threshold_seismic_out = threshold_node.add_output_port(endpoint=output_seismic_thresold_address)
threshold_notify_out = threshold_node.add_output_port("We found what we were looking for !!!",
                                                      endpoint=output_threshold_notify_address)
notify_in = notify_node.add_input_port(def_notification_method, endpoint=input_notify_address)

my_workflow.add_node(seismic_node)
my_workflow.add_node(threshold_node)
my_workflow.add_node(notify_node)

my_workflow.add_edge(Transport.ZMQ_TCP, Transport.JSON, seismic_out, threshold_in)
my_workflow.add_edge(Transport.UDP, Transport.PICKLE, threshold_seismic_out, seismic_in)
my_workflow.add_edge(Transport.Multicast, Transport.JSON, threshold_notify_out, notify_in, multicast_address)

try:
    print("Workflow running...")
    print "Started Seismic Data Collection ... "
    my_workflow.enact()
    raw_input('Hit any key to exit the program ...\n')
except KeyboardInterrupt:
    pass


print("Workflow Finished ... ")

# Some serialisation testing

prettify=True
serialized = my_workflow.serialize(prettify)

print "The workflow Serialised Looks Like This: " + serialized

deserialized_workflow = Workflow.deserialize(serialized)

serialized = deserialized_workflow.serialize()
