import logging
import threading

import mgen
from Transport import Transport


__author__ = "Ian Taylor <ian.j.taylor@gmail.com>"
__license__ = "None"

# UDP Server Code

interrupted = False


class MGENMulticastServer():

    @Transport.initialise_server
    def __init__(self, target_method, bind_address="localhost", bind_port=5354,
                 multicast_address="224.1.2.3", multicast_port=5459):
        self.is_running = False
        self.target_method = target_method
        self.logger = logging.getLogger('MGENServer')
        self.logger.debug('__init__')

        self.bind_address = bind_address

        self.bind_port = bind_port
        self.mymgen=mgen.Controller()
        self.mymgen.send_command("ipv4")

        join_command="join " + str(multicast_address) + " port " + str(multicast_port) + " interface " + bind_address
        self.mymgen.send_event(join_command)
        listen_command = "listen udp " + str(multicast_port) + " interface " + multicast_address
        self.mymgen.send_event(listen_command)

    def receive(self):
        """ Worker routine """
        self.is_running = True

        try:
            for line in self.mymgen:
                #print "MGEN Listening"

                if not self.is_running:
                    break
                event = mgen.Event(line)
                print line
                print event.rx_time, event.size
                if event.type == 0:
                    if event.data is not None:
                       payload = event.data
                       #print "got it"
                       #print payload
                      # print "MGEN Message Received: "
                       self.handle_message(self.target_method, payload, None)
        except RuntimeError as err:
            self.logger.error("Error from MGEN socket server: " + err.message)

    @Transport.handle_message
    def handle_message(self, target_method, data, client_address):
        return data

    def start(self):
        t = threading.Thread(target=self.receive)
        t.setDaemon(True) # don't hang on exit
        t.start()

    def close(self):
        self.is_running = False
        self.mymgen = None


class MGENMulticastClient():

    @Transport.initialise_client
    def __init__(self, bind_address, bind_port, mult_address, multi_port):
        self.logger = logging.getLogger('ZMQServer')
        self.logger.debug('__init__')

        self.bind_address = bind_address
        self.bind_port = bind_port

        self.multicast_address = mult_address
        self.multicast_port = multi_port

        self.mgen_sender = mgen.Controller("sender")

    @Transport.send
    def send(self, message):
        mgen_message = "on 1 udp dst " + self.multicast_address + "/" + str(self.multicast_port) + \
                            " per [1 1024] count 1 interface " + self.bind_address + \
                            " data [%s] count 10" % message.encode('hex','strict').rstrip()

       # print "Sending message using command " + mgen_message

        self.mgen_sender.send_event(mgen_message)

    def close(self):
        del self.mgen_sender


def test_method(transport_class, *args, **kwargs):
    print "In test target method, Data is :\n"
    print str(args) +  str(kwargs)
    transport_class.close()

if __name__ == '__main__':
    mgenClient = MGENMulticastClient("localhost", 4545, "224.0.1.186", 5000)
    mgenServer = MGENMulticastServer(test_method, "localhost", 4546,  "224.0.1.186", 5000)

    try:
        mgenServer.start()
        print("MGEN Example Server running...")
        mgenClient.send("sensor1_data", "sensor2_data", sensor1=[1, 2, 3, 4, 5], sensor2=[5, 6, 7, 8, 9])
        raw_input('Hit any key to quit')
    except KeyboardInterrupt:
        pass

    mgenClient.close()
    mgenServer.close()
