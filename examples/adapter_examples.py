from newt.wire.Adapter import Adapter
from newt.wire.Transport import Transport

import logging
import time


"""
Tests for the three protocols implemented showing a UDP sender and receiver, a ZMQ
sender and receiver and a multicast sender and three receivers.
"""


def test_method(transport_class, *args, **kwargs):
    print "In test target method for " + transport_class.__class__.__name__ + ", Data received is :"

    for i in range(len(args)):
        print args[i]

    for key, value in kwargs.iteritems():
        print "%s = %s" % (key, value)

    transport_class.close() # close each receiver after one receive.


logging.basicConfig(level=logging.INFO)

adapter = Adapter(Transport.UDP, Transport.JSON)
uc = adapter.get_receiver_instance(test_method, "localhost", 4545)
us = adapter.get_sender_instance("localhost", 4546, "localhost", 4546)
uc.start()
us.send("one", "two", "three", "...", first_name="Ian", last_name="Taylor")
time.sleep(1)

adapter = Adapter(Transport.ZMQ_TCP, Transport.JSON)
zc = adapter.get_receiver_instance(test_method, "localhost", 4546)
zs = adapter.get_sender_instance("localhost", 4545, "localhost", 4546)
zc.start()
zs.send("one", "two", "three", "...", first_name="Ian", last_name="Taylor")
time.sleep(1)


adapter = Adapter(Transport.Multicast, Transport.PICKLE)
ms = adapter.get_sender_instance("localhost", 4545, "224.1.2.3", 5353)
mr1 = adapter.get_receiver_instance(test_method, "localhost", 4548, "224.1.2.3", 5353)
mr2 = adapter.get_receiver_instance(test_method, "localhost", 4549, "224.1.2.3", 5353)
mr3 = adapter.get_receiver_instance(test_method, "localhost", 4550, "224.1.2.3", 5353)
mr1.start()
mr2.start()
mr3.start()
ms.send("one", "two", "three", "...", first_name="Ian", last_name="Taylor")
time.sleep(5)

uc.close()
ms.close()
zc.close()