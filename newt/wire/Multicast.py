
__author__ = 'Ian Taylor'

import socket
import struct
import logging
import threading
from Transport import Transport
import net.Network as net

class Multicast(object):
    bind_port = None
    bind_address = None
    multicast_group = None
    sock = None
    ttl = 100
    max_payload = 1000000

    def __init__(self, bind_address="INADDR_ANY", bind_port=5354, multicast_address="224.1.2.3", multicast_port=5355):

        if bind_address == "localhost":
            self.bind_address = net.get_local_ip_address()
        else:
            self.bind_address = bind_address
        self.bind_port = bind_port
        self.multicast_address= multicast_address
        self.multicast_port = multicast_port

        self.multicast_group = (multicast_address, multicast_port)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

        try:
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)
        except AttributeError:
            pass

        if hasattr(self.sock, 'SO_REUSEPORT'):
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, True)

        ttl = struct.pack('b', Multicast.ttl)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    def close(self):
            # Clean up
        self.sock.close()
        self.sock = None

class MulticastReceiver(Multicast):

    @Transport.initialise_server
    def __init__(self, target_method, bind_address="INADDR_ANY", bind_port=5354, multicast_address="224.1.2.3", multicast_port=5355):
        super(MulticastReceiver, self).__init__(str(bind_address), int(bind_port), str(multicast_address), int(multicast_port))
        self.target_method = target_method
        self.logger = logging.getLogger('Multicast Listener')

    def start(self):
        t = threading.Thread(target=self.run)
        t.setDaemon(True) # don't hang on exit
        t.start()

    def run(self):

        self.logger.debug("binding to: " + str(self.bind_address) + "/" + str(self.bind_port))

        self.sock.bind(self.multicast_group)

        group = socket.inet_aton(self.multicast_address) + socket.inet_aton(self.bind_address)

        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, group)

        while self.sock is not None:
            self.logger.debug('listening to MC group: ' + self.multicast_address + ", port: " + str(self.multicast_port))
            data, address = self.sock.recvfrom(self.max_payload)

            self.sender_address = address
            self.logger.debug('received %s bytes from %s' % (len(data), address))
            self.logger.debug(data)

            self.handle_message(self.target_method, data, address)

    @Transport.handle_message
    def handle_message(self, target_method, data, client_address):
        return data


class MulticastSender(Multicast):

    @Transport.initialise_client
    def __init__(self, bind_address="INADDR_ANY", bind_port=5354, multicast_address="224.1.2.3", multicast_port=5355):
        super(MulticastSender, self).__init__(str(bind_address), int(bind_port), str(multicast_address), int(multicast_port))
        self.logger = logging.getLogger('Multicast Sender')
        self.logger.debug('multicast DNS created')

        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)

        bindingto = (str(self.bind_address), 0)

        self.logger.debug("binding to: " + str(self.bind_address) + "/" + str(self.bind_port))

        self.sock.bind(bindingto)

    @Transport.send
    def send(self, message):
        # Send data to the multicast group
        self.logger.debug('sending "%s"' % message)
        self.logger.debug('To "%s"' % str(self.multicast_group))
        sent = self.sock.sendto(message, self.multicast_group)

        self.logger.debug("Sent: " + str(sent))



def test_method(transport_class, *args, **kwargs):
    print "In test target method, Data is :\n"
    print str(args) +  str(kwargs)
    transport_class.close()

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    ts = MulticastSender("localhost", 4545, "224.1.2.3", 5353)
    tr = MulticastReceiver(test_method, "localhost", 4548, "224.1.2.3", 5353)

    print("Multicast Example Server running...")
    tr.start()
    ts.send("one", "two", "three", "...", first_name="ian", last_name="Taylor")
    import time
    time.sleep(1)
    ts.close()

