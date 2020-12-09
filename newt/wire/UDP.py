import socket
import logging
import SocketServer
import threading
import net.Network as network
from Transport import Transport

import net.Network
__author__ = "Ian Taylor <ian.j.taylor@gmail.com>"


class RequestHandler(SocketServer.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger('UDPRequestHandler')
        self.logger.debug('__init__')
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)

    def handle(self):
        data = self.request[0].strip()
        self.socket = self.request[1]
        self.logger.debug("{} sent: ".format(self.client_address[0]))
        self.logger.debug(data)
        self.server.message_received(data, self.client_address[0])


class UDPServer(SocketServer.UDPServer):

    @Transport.initialise_server
    def __init__(self, target_method, bind_address="INADDR_ANY", bind_port=5354):
        self.is_running = False
        self.target_method = target_method
        self.logger = logging.getLogger('UDPServer')
        localhost = network.get_local_ip_address()
        self.logger.debug('UDP __init__ for host ' + localhost + ' using bind address: ' + bind_address + "/" + str(bind_port))
        SocketServer.UDPServer.allow_reuse_address = True
        SocketServer.UDPServer.__init__(self, (str(bind_address), int(bind_port)), RequestHandler)
        return


    def server_activate(self):
        self.logger.debug('server_activate')
        SocketServer.UDPServer.server_activate(self)
        return

    def run(self):
        self.is_running = True
        self.serve_forever()

    def start(self):
        t = threading.Thread(target=self.run)
        t.setDaemon(True) # don't hang on exit
        t.start()

    def message_received(self, data, client_address):
        self.handle_message(self.target_method, data, client_address)

    @Transport.handle_message
    def handle_message(self, target_method, data, client_address):
        self.logger.debug('handle_message')
        return data

    def handle_request(self):
        self.logger.debug('handle_request')
        return SocketServer.UDPServer.handle_request(self)

    def verify_request(self, request, client_address):
        self.logger.debug('verify_request(%s, %s)', request, client_address)
        return SocketServer.UDPServer.verify_request(self, request, client_address)

    def process_request(self, request, client_address):
        self.logger.debug('process_request(%s, %s)', request, client_address)
        return SocketServer.UDPServer.process_request(self, request, client_address)

    def server_close(self):
        self.logger.debug('server_close')
        return SocketServer.UDPServer.server_close(self)

    def finish_request(self, request, client_address):
        self.logger.debug('finish_request(%s, %s)', request, client_address)
        return SocketServer.UDPServer.finish_request(self, request, client_address)

    def close_request(self, request_address):
        self.is_running=False
      #  self.logger.debug('close_request(%s)', request_address)
        return SocketServer.UDPServer.close_request(self, request_address)

    def close(self):
    # Clean up
        self.is_running = False
        SocketServer.UDPServer.server_close(self)
        self.logger.debug('Closed socket')


class UDPClient():

    @Transport.initialise_client
    def __init__(self, bind_address="INADDR_ANY", bind_port=5354, dest_address="localhost", dest_port=5354):

        self.logger = logging.getLogger('UDPClient')
        self.logger.debug('__init__')
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        bind_port = int(bind_port)
        bind_address = str(bind_address)
        binding = True
        while binding:
            try:
                self.logger.debug("Binding to : " + bind_address + " / " + str(bind_port))
                self.sock.bind((bind_address, bind_port))
                binding = False
            except socket.error as err:
                bind_port += 1

        self.dest_address = str(dest_address)
        self.dest_port = int(dest_port)


    @Transport.send
    def send(self, message):
        localhost = network.get_local_ip_address()
        self.logger.debug('UDP send for host ' + localhost + ", message: " + message)
        self.logger.debug("To: " + self.dest_address + " / " + str(self.dest_port))
        self.sock.sendto(message, (self.dest_address, self.dest_port))

    def close(self):
        self.logger.debug('closing UDP listener')
        self.sock.close()
        self.logger.debug('done')


def test_method(transport_class, *args, **kwargs):
    print "In test target method, Data is :\n"
    print str(args) +  str(kwargs)


if __name__ == '__main__':
    tc = UDPClient("localhost", 4545, "localhost", 4546)
    ts = UDPServer(test_method, "localhost", 4546)

    try:
        ts.start()
        tc.send("one", "two", ian="ian", John="john")
        print("UDP Example Server running...")
        raw_input('Hit any key to quit')
    except KeyboardInterrupt:
        pass

    import time
    time.sleep(3)
    tc.close()
    ts.close()

