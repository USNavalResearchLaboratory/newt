from Transport import Transport
from Multicast import MulticastReceiver, MulticastSender
from UDP import UDPServer, UDPClient
from ZMQ import ZMQServer, ZMQClient
from MGEN import MGENServer, MGENClient
from MGENMulticast import MGENMulticastServer, MGENMulticastClient


class Adapter():

    serialisation = None
    transport = None
    workflow = None

    def __init__(self, transport, serialisation, workflow=None):
        self.transport = transport
        self.serialisation = serialisation
        self.workflow = workflow

    def get_sender_instance(self, bind_address, bind_port, dest_address, dest_port):
        if self.transport == Transport.UDP:
            sender = UDPClient(bind_address, bind_port, dest_address, dest_port)
        elif self.transport == Transport.Multicast:
            sender = MulticastSender(bind_address, bind_port, dest_address, dest_port)
        elif self.transport == Transport.ZMQ_TCP:
            sender = ZMQClient(bind_address, bind_port, dest_address, dest_port)
        elif self.transport == Transport.MGEN:
            sender = MGENClient(bind_address, bind_port, dest_address, dest_port)
        elif self.transport == Transport.MGENMulticast:
            sender = MGENMulticastClient(bind_address, bind_port, dest_address, dest_port)
        else:
            raise Exception("Sorry Transport protocol not found")

        sender.serialisation = self.serialisation
        sender.workflow = self.workflow
        return sender

    def get_receiver_instance(self, target_method, bind_address, bind_port,
                     multicast_address=None, multicast_port=None):
        if self.transport == Transport.UDP:
            receiver = UDPServer(target_method, bind_address, bind_port)
        elif self.transport == Transport.Multicast:
            receiver = MulticastReceiver(target_method, bind_address, bind_port,
                                         multicast_address, multicast_port)
        elif self.transport == Transport.ZMQ_TCP:
            receiver = ZMQServer(target_method, bind_address, bind_port)
        elif self.transport == Transport.MGEN:
            receiver = MGENServer(target_method, bind_address, bind_port)
        elif self.transport == Transport.MGENMulticast:
            receiver = MGENMulticastServer(target_method, bind_address, bind_port,
                                         multicast_address, multicast_port)
        else:
            raise Exception("Sorry Transport protocol not found")

        receiver.serialisation = self.serialisation
        receiver.workflow = self.workflow
        return receiver

