__author__ = 'scmijt'

from newt.wire.Transport import Transport
from newt.Workflow import Workflow, Node, Edge, Port

import logging

count = 0


def sensor_collect(transport, *args, **kwargs):
    print "Seismic node: using transport " + transport.__class__.__name__
    print "Seismic Node: Collecting more sensor information... workflow looping is working :)"


def decision_method(transport, *args, **kwargs):
    ports = transport.workflow.get_my_output_ports(transport)
    feed_back = ports[0]
    notify = ports[1]

    print "Decision node: using transport " + transport.__class__.__name__

    decision_method.count += 1

    if decision_method.count > 5:
        print "Decision Node: Received Sensor Data And Threshold Met !!!!"
        print "Decision Node: Setting notification to be enabled to send to Notification Node!"
        feed_back.enabled = False
        notify.enabled = True
    else:
        print "Decision Node: Received Sensor Data But Data Threshold Not Met"
        print "Decision Node: looping back to the Seismic Sensor Node"
        feed_back.enabled = True
        notify.enabled = False

# Initialise count
decision_method.count = 0  # Interesting ! python can have static counts on methods ...


def notification_method(transport, *args, **kwargs):
    print "Notification node: using transport " + transport.__class__.__name__ + ", I received this notification:"

    for i in range(len(args)):
        print args[i]

    for key, value in kwargs.iteritems():
        print "%s = %s" % (key, value)

logging.basicConfig(level=logging.INFO)

seismic_address = ("localhost", 5352)
threshold_address = ("localhost", 5454)
notify_address = ("localhost", 5455)
sender_address_seismic = ("localhost", 5456)
sender_address_threshold_seismic = ("localhost", 5457)
sender_address_threshold_notify = ("localhost", 5458)
multicast_address = ("224.1.2.3", 5459)


my_workflow = Workflow("My First Workflow")

node_seismic = Node("Seismic_Sensor", sensor_collect)
node_seismic.initiator = True  # Mark this as a start node for the workflow even though it has a receive port.
receiver_seismic = node_seismic.add_receiver(seismic_address)
sender_seismic = node_seismic.add_sender(sender_address_seismic, threshold_address)
sender_seismic.set_send_data("one", "two", "three", "...", first_name="Ian", last_name="Taylor")

node_threshold = Node("Threshold_detection", decision_method)
receiver_threshold = node_threshold.add_receiver(threshold_address)
sender_for_threshold_seismic = node_threshold.add_sender(sender_address_threshold_seismic, seismic_address)
sender_for_threshold_seismic.set_send_data("Go Again")
sender_for_threshold_notify = node_threshold.add_sender(sender_address_threshold_notify, multicast_address)
sender_for_threshold_notify.set_send_data("We found what we were looking for !!!")

node_notify = Node("Notify", notification_method)
receiver_notify = node_notify.add_receiver(notify_address, multicast_address)

my_workflow.add_node(node_seismic)
my_workflow.add_node(node_threshold)
my_workflow.add_node(node_notify)

my_workflow.configure_path(sender_seismic, receiver_threshold, Transport.ZMQ_TCP, Transport.JSON)
my_workflow.configure_path(sender_for_threshold_seismic, receiver_seismic, Transport.UDP, Transport.PICKLE)
my_workflow.configure_path(sender_for_threshold_notify, receiver_notify, Transport.MGEN, Transport.MGEN)

try:
    print("Workflow running...")
    print "Started Seismic Data Collection ... "
    my_workflow.enact()
    raw_input('Hit any key to exit the program ...\n')
except KeyboardInterrupt:
    pass


print("Workflow Finished ... ")

# Some serialisation testing

ser = my_workflow.serialize()

print "The workflow Serialised Looks Like This: " + ser

deserialized_workflow = Workflow.deserialize(ser)

ser = deserialized_workflow.serialize()
