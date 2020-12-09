from newt.wire.Adapter import Adapter
from newt.wire.Transport import Transport

import logging
import time


"""
Multicast receive, to udp send.
"""

def udp_method(transport_class, *args, **kwargs):
    print "In UDP target method for " + transport_class.__class__.__name__ + ", Data received is :"

    for i in range(len(args)):
        print args[i]

    for key, value in kwargs.iteritems():
        print "%s = %s" % (key, value)

   # transport_class.close() # close each receiver after one receive.

#set up the UDP sender and receivers.

adapter = Adapter(Transport.UDP, Transport.JSON)
uc = adapter.get_receiver_instance(udp_method, "localhost", 4545)
us = adapter.get_sender_instance("localhost", 4546, "localhost", 4545)
uc.start()

def proxy_method(transport_class, *args, **kwargs):

    print "In proxy target method for " + transport_class.__class__.__name__ + ", Data received is :"

    for i in range(len(args)):
        print args[i]

    for key, value in kwargs.iteritems():
        print "%s = %s" % (key, value)

    time.sleep(2)

    print "UDP Socket connection sending message"

    us.send("oh", "my", "multicast proxy works", "...", protocol="Multicast", sender="localhost")

   # transport_class.close()  # close MC connection

logging.basicConfig(level=logging.INFO)

adapter = Adapter(Transport.Multicast, Transport.PICKLE)
ms = adapter.get_sender_instance("localhost", 4547, "224.1.2.3", 5353)
mr = adapter.get_receiver_instance(proxy_method, "localhost", 4547, "224.1.2.3", 5353)
mr.start()


time.sleep(1)
ms.send("one", "two", "three", "...", protocol="Multicast", sender="localhost")


time.sleep(3)
#uc.close()
#ms.close()
