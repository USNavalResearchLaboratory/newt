import logging
import threading

import zmq
from Transport import Transport


__author__ = "Ian Taylor <ian.j.taylor@gmail.com>"
__license__ = "None"

# UDP Server Code

interrupted = False


class ZMQServer():
    cache = []
    queue_size = 10
    protocol = "tcp"

    @Transport.initialise_server
    def __init__(self, target_method, bind_address="*", bind_port=5354):
        self.is_running = False
        self.target_method = target_method
        self.logger = logging.getLogger('ZMQServer')
        self.logger.debug('__init__')

        if bind_address == "localhost":
            self.bind_address = "*"
        else:
            self.bind_address = bind_address
        self.bind_port = bind_port
        self.context = zmq.Context()
        self.server = self.context.socket(zmq.PULL)

        self.protocol = ZMQServer.protocol
        bind_string = self.protocol + '://' + self.bind_address + ':' + str(self.bind_port)
        self.logger.debug("Binding to " + bind_string)
        self.server.bind(bind_string)

    def receive(self):
        """ Worker routine """
        self.is_running = True

        try:
            while self.is_running:
                data = self.server.recv()
                self.handle_message(self.target_method, data, None)
        except RuntimeError as err:
            self.logger.error("Error from ZMQ socket server: " + err.message)

    @Transport.handle_message
    def handle_message(self, target_method, data, client_address):
        return data

    def start(self):
        t = threading.Thread(target=self.receive)
        t.setDaemon(True) # don't hang on exit
        t.start()

    def close(self):
        self.is_running = False
        self.server.close()
        self.context.term()


class ZMQClient():
    queue_size = 10
    protocol = "tcp"

    @Transport.initialise_client
    def __init__(self, bind_address, bind_port, dest_address, dest_port):
        self.logger = logging.getLogger('ZMQServer')
        self.logger.debug('__init__')

        if (bind_address == "localhost"):
            self.bind_address = "*"
        else:
            self.bind_address = bind_address
        self.bind_port = bind_port
        self.dest_address = dest_address
        self.dest_port = dest_port
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUSH)
        self.socket.setsockopt(zmq.SNDHWM, self.queue_size)
        bindstring = self.protocol + '://' + self.bind_address + ':' + str(self.bind_port)
        self.logger.debug("Binding to " + bindstring)
        self.socket.bind(bindstring)
        self.socket.connect(self.protocol + '://' + self.dest_address + ':' + str(self.dest_port))

    @Transport.send
    def send(self, message):
        self.socket.send(message)

    def close(self):
        self.socket.close()
        self.context.term()

def test_method(transport_class, *args, **kwargs):
    print "In test target method, Data is :\n"
    print str(args) +  str(kwargs)
    transport_class.close()

if __name__ == '__main__':
    zmqClient = ZMQClient("localhost", 4545, "localhost", 4546)
    zmqServer = ZMQServer(test_method, "localhost", 4546)

    try:
        zmqServer.start()
        zmqClient.send("one", "two", ian="ian", John="john")
        print("ZMQ Example Server running...")
        raw_input('Hit any key to quit')
    except KeyboardInterrupt:
        pass

    zmqClient.close()
    zmqServer.close()
