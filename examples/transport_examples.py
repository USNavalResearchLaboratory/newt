from newt.wire.Multicast import MulticastReceiver, MulticastSender
from newt.wire.UDP import UDPServer, UDPClient
from newt.wire.ZMQ import ZMQServer, ZMQClient

import logging
import time


"""
Tests for the three protocols implemented showing a UDP sender and receiver, a ZMQ
sender and receiver and a multicast sender and three receivers.
"""


def test_method(transport_class, *args, **kwargs):
    print "Transport " + transport_class.__class__.__name__

    for i in range(len(args)):
        print args[i]

    for key, value in kwargs.iteritems():
        print "%s = %s" % (key, value)

    transport_class.close() # close each receiver after one receive.


logging.basicConfig(level=logging.INFO)

uc = UDPClient("localhost", 4545, "localhost", 4546)
us = UDPServer(test_method, "localhost", 4546)
us.start()
uc.send("one", "two", "three", "...", first_name="Ian", last_name="Taylor")
time.sleep(1)

zc = ZMQClient("localhost", 4545, "localhost", 4546)
zs = ZMQServer(test_method, "localhost", 4546)
zs.start()
zc.send("one", "two", "three", "...", first_name="Ian", last_name="Taylor")
time.sleep(1)

from newt.wire.Multicast import MulticastReceiver, MulticastSender
from newt.wire.Transport import Transport

Transport.serialization = Transport.PICKLE

ms = MulticastSender("localhost", 4545, "224.1.2.3", 5353)
mr1 = MulticastReceiver(test_method, "localhost", 4548, "224.1.2.3", 5353)
mr2 = MulticastReceiver(test_method, "localhost", 4549, "224.1.2.3", 5353)
mr3 = MulticastReceiver(test_method, "localhost", 4550, "224.1.2.3", 5353)
mr1.start()
mr2.start()
mr3.start()
ms.send("one", "two", "three", "...", first_name="Ian", last_name="Taylor")
time.sleep(1)

uc.close()
ms.close()
zc.close()