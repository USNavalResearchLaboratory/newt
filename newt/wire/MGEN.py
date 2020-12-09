import logging
import threading

import mgen
from Transport import Transport


__author__ = "Ian Taylor <ian.j.taylor@gmail.com>"
__license__ = "None"

# UDP Server Code

interrupted = False


class MGENServer():

    @Transport.initialise_server
    def __init__(self, target_method, bind_address="localhost", bind_port=5354):
        self.is_running = False
        self.target_method = target_method
        self.logger = logging.getLogger('MGENServer')
        self.logger.debug('__init__')

        self.bind_address = bind_address
        self.bind_port = bind_port
        self.mymgen=mgen.Controller()
        self.mymgen.send_command("ipv4")

        # listen_command = "listen udp " + str(bind_address) + " interface " + str(bind_port) + " LOG /tmp/mgen.drc"
        listen_command = "listen udp " + str(bind_port) + " output /tmp/mgen.drc"
        print "Receiving usign event " + listen_command
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


class MGENClient():

    @Transport.initialise_client
    def __init__(self, bind_address, bind_port, dest_address="localhost", dest_port=5354):
        self.logger = logging.getLogger('MGEN')
        self.logger.debug('__init__')

        self.bind_address = bind_address
        self.bind_port = bind_port
        self.dest_address = str(dest_address)
        self.dest_port = int(dest_port)

        self.mgen_sender = mgen.Controller("sender" + str(bind_port))
        self.mgen_sender.send_command("ipv4")

    @Transport.send
    def send(self, message):
        mess_binary = message.encode('hex','strict').rstrip()
        mgen_message = "on 1 udp dst " + self.dest_address + "/" + str(self.dest_port) + \
                            " PERIODIC [1 " + str(len(mess_binary)+1) + "] count 1 " + \
                            " data [%s]" % mess_binary

        print "Sending message using event " + mgen_message

        self.mgen_sender.send_event(mgen_message)

    def close(self):
        del self.mgen_sender


def test_method(transport_class, *args, **kwargs):
    print "In test target method, Data is :\n"
    print str(args) +  str(kwargs)
    transport_class.close()

if __name__ == '__main__':
    mgenClient = MGENClient("localhost", 4545)
    mgenServer = MGENServer(test_method, "localhost")

    try:
        mgenServer.start()
        print("MGEN Example Server running...")
        mgenClient.send("sensor1_data", "sensor2_data", sensor1=[1, 2, 3, 4, 5], sensor2=[5, 6, 7, 8, 9])
        raw_input('Hit any key to quit')
    except KeyboardInterrupt:
        pass

    mgenClient.close()
    mgenServer.close()
