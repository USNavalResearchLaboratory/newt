__author__ = 'scmijt'

from wire.Adapter import Adapter
from wire.Transport import Transport
import logging
import wire.net.Network as net
import socket

import inspect


class Endpoint:
    address = None
    port = None

    def __init__(self, address="localhost", port=socket.INADDR_ANY):
        self.address = address
        self.port = port

    def parameters(self):
        parameters = dict()
        parameters["address"] = self.address
        parameters["port"] = self.port
        return parameters

    @staticmethod
    def get_endpoint_from_parameters(parameters):
        address = parameters["address"]
        port = parameters["port"]

        return Endpoint(address, port)


"""
The base workflow class for representing workflows and serializing and deserializing them. Workflows
consist of nodes that have ports (like network adapters/addresses) which connect to other ports on
other nodes using edges.
"""


class Workflow:
    nodes = None
    edges = None
    name = None
    include_args=None

    SIGMA_SERIALIZATION = False

    def __init__(self, name=None):
        self.name = name
        self.nodes = []
        self.edges = []
        self.logger = logging.getLogger('Workflow')

    def add_node(self, node):
        self.nodes.append(node)
        node.workflow=self

    def get_node(self, unique_name):
        for node in self.nodes:
            if node.unique_name == unique_name:
                return node
        return None

    def get_port(self, unique_name, port_id):
        for node in self.nodes:
            if node.unique_name == unique_name:
                return node.get_port(port_id)
        return None

    def add_edge(self, transport, serialization, out_port, in_port, multicast_endpoint=None):
        edge = Edge(transport, serialization, out_port, in_port, multicast_endpoint)
        if edge not in self.edges:
            self.edges.append(edge)
            return edge
        return None

    def add_edge_obj(self, edge):
        self.edges.append(edge)
        return edge

    def get_edge_for_port(self, port_id):
        for edge in self.edges:
            if edge.in_port.port_id == port_id or edge.out_port.port_id == port_id:
                return edge
        return None

    def get_node_for_port(self, port):
        for node in self.nodes:
            if node.has_port(port.port_id):
                return node
        return None

    def serialize(self, prettify=False):
        items = dict()
        nodes = []
        edges = []

        if Workflow.SIGMA_SERIALIZATION:
            for node in self.nodes:
                nodes.append(node.sigma_serialize())
            for edge in self.edges:
                edges.append(edge.sigma_serialize())
        else:
            for node in self.nodes:
                nodes.append(node.parameters())
            for edge in self.edges:
                edges.append(edge.parameters())

            if self.name is not None:
                items["name"] = self.name

        self.logger.debug(str(nodes))
        self.logger.debug(str(edges))

        items["nodes"] = nodes
        items["edges"] = edges
        return JSON.serialize_dic(items, prettify)

    @staticmethod
    def deserialize(json):

        workflow = Workflow()
        items = JSON.deserialize(json)

        if "name" in items:
            workflow.name = items["name"]

        nodes = items["nodes"]
        edges = items["edges"]

        for node_params in nodes:
            node = Node.get_node_from_parameters(node_params)
            node.workflow = workflow
            workflow.add_node(node)

        for edge_params in edges:
            workflow.add_edge_obj(Edge.get_edge_from_parameters(edge_params, workflow))

        return workflow

    def enact(self):
        # first enact all receivers
        for node in self.nodes:
            for port in node.ports:
                if node.is_on_my_host() and isinstance(port, InputPort):
                    edge = self.get_edge_for_port(port.port_id)
                    if edge is not None: # only start receivers that are connected, otherwise we treat them as methods
                        receiver_adapter = Adapter(edge.transport, edge.serialization, self)
                        receiver = receiver_adapter.get_receiver_instance(port.get_target_method(), port.bind_address,
                                                                          port.bind_port, edge.get_receiver_address(),
                                                                          edge.get_receiver_port())
                        self.logger.debug( "Host " + node.unique_name + " has created input port for target method " + \
                              str(port.target_method) + " on address " + receiver.bind_address + "/" + str(receiver.bind_port))
                        port.bind_address = receiver.bind_address
                        port.bind_port = receiver.bind_port
                        self.logger.debug("Starting receiver on node " + node.unique_name + " using target_method " +
                                          str(port.target_method))
                        receiver.start()

        # temp sleep allow the bootstrapping of the receivers for decentralised nodes - need a better way perhaps??? !!!
        import time
        print("Waiting 5 seconds for the receiver ports to initialise...")
        time.sleep(10)
        print("Continuing...")

        # then look for send only nodes (those without input ports) or those that have the initiator flag set
        for node in self.nodes:
            self.logger.debug ("Node = " + node.unique_name + " is initiator: " + str(node.initiator))
            if node.is_on_my_host() and node.initiator:
                self.logger.debug ("Args = " + str(node.initiator_args))
                self.logger.debug ("Kwargs = " + str(node.initiator_kwargs))

                target_method = node.get_target_method() # the binding is already done to the target method
                                                     # so we do not need to worry about multiple ports.

                return_values = target_method(node, *node.initiator_args, **node.initiator_kwargs)
                self.logger.debug("Returned vals are " + str(return_values))

                for port in node.ports:
                    if isinstance(port, OutputPort) and port.enabled:
                        self.send_output_from_node_and_port(node,port,return_values)

    def send_output_from_node_and_port(self, node, port, return_values=None):
        edge = self.get_edge_for_port(port.port_id)

        sender_adapter = Adapter(edge.transport, edge.serialization, self)
        self.logger.debug("Creating sender " + str(port.bind_address) + "/" + str(port.bind_port)
                          + " to " + str(edge.get_receiver_address()) + "/" +
                          str(edge.get_receiver_port()))
        sender = sender_adapter.get_sender_instance(port.bind_address, port.bind_port,
                                                    edge.get_receiver_address(),
                                                    edge.get_receiver_port())
        # print("Port Type " + str(port.port_type))
        port.bind_address = sender.bind_address
        port.bind_port = sender.bind_port
        args = port.args
        kwargs = port.kwargs
        self.logger.debug("Sending " + str(args) + " " + str(kwargs) + " from " + node.unique_name)

        Transport.parse_arguments_and_send(sender, node, return_values, *args, **kwargs)

        return return_values

    def get_my_input_port(self, transport):
        return self.get_input_port_for_server_with(transport.bind_address, transport.bind_port)

    def get_input_port_for_server_with(self, bind_address, bind_port):
        # self.logger.debug("Finding output ports with bind address " + bind_address + " and port " + str(bind_port))
        for node in self.nodes:
            for port in node.ports:
                if isinstance(port, InputPort) and port.bind_address == bind_address \
                        and port.bind_port == bind_port:
                    return port
        return None


    def get_my_node(self, transport):
        for node in self.nodes:
            for port in node.ports:
                if isinstance(port, InputPort) and port.bind_address == transport.bind_address \
                        and port.bind_port == transport.bind_port:
                    return node
        return None

    def clean_up(self):
        for edge in self.edges:
            pass # need to store all open connections and clean up ...


Workflow.include_args=True

from wire.serialize.JSON import JSON


class Node:
    ports = None
    unique_name = None
    workflow = None

    # The initiator flag is used to specify that this node is the start point for the workflow. This is used
    #  in the case a node has an receive port but is still supposed to initiate the workflow
    #  e.g. it could receive feedback also from other components to form a cyclic loop

    initiator = False
    initiator_args = None
    initiator_kwargs = None
    initiator_target_method= None

    def __init__(self, unique_name, initiator=False):
        self.unique_name = unique_name
        self.logger = logging.getLogger('Node')
        self.ports = []
        self.initiator = initiator

    target_method = None

    def set_initiator_method_and_args(self, target_method, *args, **kwargs):

        if self.initiator_target_method is not None:
            return # do not set once set up for this node - hack to avoid complexity in hamlet but need a better way.

        if target_method is not None:
            if not isinstance(target_method, basestring):
                import sys
                target_module = sys.modules[target_method.__module__]
                target_method = target_module.__name__ + "." + target_method.__name__

        self.initiator_target_method = target_method
        self.initiator_args= list(args)
        self.initiator_kwargs = dict(kwargs)

    def get_target_method(self):
        if self.initiator_target_method is None:
            from Exceptions import NoTargetDefinedException
            raise NoTargetDefinedException(
                "No target method defined for initiator node " + self.unique_name)

        items = self.initiator_target_method.split(".")
        fn_mod = __import__(items[0])
        fn = getattr(fn_mod, items[1])
        return fn


    def is_on_my_host(self):
        local_address = net.get_local_ip_address()
        self.logger.debug("Local address is " + local_address)

        for port in self.ports:
           # self.logger.debug("Comparing with port type " + port.port_type + ", bind address " +
            #                  port.bind_address)
#            if port.port_type == Port.RECEIVE_PORT and (port.bind_address == local_address
 #                                                       or net.is_a_local_address(port.bind_address)):
            if port.bind_address == local_address or net.is_a_local_address(port.bind_address):
                self.logger.debug("I matched " + local_address + " with " + port.port_type + ", bind address " +
                              port.bind_address)
#
                return True

        return False

    def get_host(self):
        return net.get_local_ip_address()

    def add_output_port(self, *args, **kwargs):
        if "endpoint" in kwargs:
            endpoint = kwargs['endpoint']
            del kwargs['endpoint']
        else:
            endpoint = Endpoint()
        port = OutputPort(self, endpoint.address, endpoint.port, *args, **kwargs)
        port.node = self
        self.ports.append(port)
        return port

    def add_output_port_detail(self, bind_address, bind_port, *args, **kwargs):
        port = OutputPort(self, bind_address, bind_port, *args, **kwargs)
        port.node = self
        self.ports.append(port)
        return port

    def add_port_obj(self, port):
        self.ports.append(port)
        port.node = self
        return port

    def add_input_port(self, target_method, *args, **kwargs):
        self.logger.debug("RECEIVE PORT BEING CREATED BY " + self.unique_name)

        if "endpoint" in kwargs:
            endpoint = kwargs['endpoint']
            del kwargs['endpoint']
        else:
            endpoint = Endpoint()

        port = InputPort(self, endpoint.address, endpoint.port, target_method, *args, **kwargs)

        port.node = self
        self.ports.append(port)
        return port

    def add_input_port_detail(self, bind_address, bind_port, target_method):
        port = InputPort(self, bind_address, bind_port, target_method)
        port.node = self
        self.ports.append(port)
        return port

    def has_port(self, port_id):
        for port in self.ports:
            if port.port_id == port_id:
                return True
        return False

    def get_port(self, port_id):
        for port in self.ports:
            if port.port_id == port_id:
                return port
        return None

    def has_receiver_ports(self):
        for port in self.ports:
            if port.port_type == Port.RECEIVE_PORT:
                return True
        return False

    def get_first_input_port(self):
        for port in self.ports:
            if port.port_type == Port.RECEIVE_PORT:
                return port
        return None

    def get_first_output_port(self):
        for port in self.ports:
            if port.port_type == Port.SEND_PORT:
                return port
        return None

    def serialize_ports(self):
        ports = dict()
        for port in self.ports:
            ports[port.port_id] = port.parameters()
        return ports

    def get_output_ports(self):
        output_ports = []
        for port in self.ports:
            if isinstance(port, OutputPort):
                output_ports.append(port)

        return output_ports

    def get_input_ports(self):
        input_ports = []
        for port in self.ports:
            if isinstance(port, InputPort):
                input_ports.append(port)

        return input_ports

    def parameters(self):
        parameters = dict()
        parameters["unique_name"] = self.unique_name
        parameters["ports"] = self.serialize_ports()
        return parameters

    x = 50
    y = 100

    def sigma_serialize(self):

        Node.x += 20
        Node.y += 10

        parameters = dict()
        parameters["id"] = self.unique_name
        parameters["label"] = self.unique_name
        parameters["color"] = "rgb(153,255,0)"
        parameters["size"] = 10.0
        parameters["x"] = Node.x
        parameters["y"] = Node.y

        return parameters

    @staticmethod
    def get_node_from_parameters(parameters):
        unique_name = parameters["unique_name"]
        node = Node(unique_name)

        ports = parameters["ports"]
        for port_id, port_params in ports.iteritems():
            port = Port.get_port_from_parameters(node, port_params)
            node.add_port_obj(port)
        return node


class Port(object):
    node = None
    SEND_PORT = "Output_Port"
    RECEIVE_PORT = "Input_Port"
    bind_address = None
    bind_port = None
    port_type = None
    port_id = None
    port_id_iterator = 1
    enabled = True
    receiver_address = None
    receiver_port = None
    args = None
    kwargs = None

    def __init__(self, node, bind_address, bind_port, *args, **kwargs):
        if bind_address is not None and bind_address == "localhost":
            bind_address = net.get_local_ip_address()

        self.bind_address = bind_address
        self.bind_port = bind_port
        self.node = node
        self.port_id = Port.port_id_iterator
        Port.port_id_iterator += 1
        self.logger = logging.getLogger('Port')
        self.args = list(args)
        self.kwargs = dict(kwargs)
        self.logger.debug("After setting in Port " + str(self.args) + " " + str(self.kwargs))

    def __eq__(self, other):
        return (isinstance(other, self.__class__)
                and self.__dict__ == other.__dict__)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(str(self.port_id))

    def parameters(self):
        parameters = dict()
        parameters["port_id"] = self.port_id
        parameters["port_type"] = self.port_type
        parameters["bind_address"] = self.bind_address
        parameters["bind_port"] = self.bind_port
        return parameters

    @staticmethod
    def get_port_from_parameters(node, parameters):
        port_id = parameters["port_id"]
        port_type = parameters["port_type"]
        bind_address = parameters["bind_address"]
        bind_port = parameters["bind_port"]

        if port_type == Port.SEND_PORT and Workflow.include_args:
            args = None
            kwargs = None
            if "args" in parameters:
                args = list(parameters["args"])
            if "kwargs" in parameters:
                kwargs = dict(parameters["kwargs"])

            if args is not None or kwargs is not None:
                port = OutputPort(node, bind_address, bind_port, args, kwargs)
            else:
                port = OutputPort(node, bind_address, bind_port)
        else:
            target_method = parameters["target_method"]
            port = InputPort(node, bind_address, bind_port, target_method)

        port.set_port_id(port_id)
        return port

    def set_port_id(self, port_id):
        self.port_id = port_id
        Port.port_id_iterator -= 1  # reset last increment if set directly after constructor


"""
    Send ports send data so they require the data or tags that will be used to pass to the method
    they send data to
"""

class OutputPort(Port):

    def __init__(self, node, bind_address, bind_port, *args, **kwargs):
        super(OutputPort, self).__init__(node, bind_address, bind_port, *args, **kwargs)
        self.port_type = Port.SEND_PORT

    def parameters(self):
        parameters = super(OutputPort, self).parameters()
        if self.args is not None:
            parameters["args"] = self.args
        if self.kwargs is not None:
            parameters["kwargs"] = self.kwargs
        return parameters


"""
    Receive ports receive data so they require the method they should pass the data to
"""


class InputPort(Port):
    target_method = None

    def __init__(self, node, bind_address, bind_port, target_method, *args, **kwargs):
        super(InputPort, self).__init__(node, bind_address, bind_port, *args, **kwargs)
        self.port_type = Port.RECEIVE_PORT
        if target_method is not None:
            if not isinstance(target_method, basestring):
                import sys
                target_module = sys.modules[target_method.__module__]
                target_method = target_module.__name__ + "." + target_method.__name__

        self.target_method = target_method

    """
    This method converts a method in the form of module.target_method into a module instance and a method instance
    for execution. The user can just specify the method itself in the interface but the code in the constructor
    works out what module it is in and stores the target_method in plain text. Once sent for execution, the
    method is reloaded so it can be called. This allows the workflow to move around the network and be serialised
    and deserialised.
    """
    def get_target_method(self):
        if self.target_method is None:
            from Exceptions import NoTargetDefinedException
            raise NoTargetDefinedException(
                "No target method defined for input port " + self.port_id +
                ". Nodes that define receive ports MUST HAVE a method defined to call when the Node receives data.")

        items = self.target_method.split(".")
        # print(str(items))
        fn_mod = __import__(items[0])
        fn = getattr(fn_mod, items[1])
        return fn

    def parameters(self):
        parameters = super(InputPort, self).parameters()
        if self.target_method is not None:
            parameters['target_method'] = self.target_method
        return parameters


class Edge:
    transport = None
    serialization = None
    out_port = None
    in_port = None
    out_node = None
    in_node = None
    multicast_endpoint = None
    sequence_id=None

    def __init__(self, transport, serialization, out_port, in_port, multicast_endpoint=None):
        self.transport = transport
        self.serialization = serialization
        self.out_node = out_port.node
        self.out_port = out_port
        self.in_port = in_port
        self.in_node = in_port.node
        self.sequence_id = Edge.sequence_iterator
        Edge.sequence_iterator+=1

        if multicast_endpoint is None:
            # wire things across so the sender knows where to send to
            self.out_port.receiver_address = in_port.bind_address
            self.out_port.receiver_port = in_port.bind_port
        else:
            # We're using multicast, so the adapter will figure it out
            self.multicast_endpoint = multicast_endpoint

    def __eq__(self, other):
        if other.out_port == self.out_port and other.in_port == self.in_port and other.out_node == self.out_node and other.in_node == self.in_node:
            return True
        else:
            return False

    def get_receiver_address(self):
        if self.multicast_endpoint is not None:
            return self.multicast_endpoint.address
        else:
            return self.out_port.receiver_address

    def get_receiver_port(self):
        if self.multicast_endpoint is not None:
            return self.multicast_endpoint.port
        else:
            return self.out_port.receiver_port

    def parameters(self):
        parameters = dict()
        parameters["transport"] = self.transport
        parameters["serialisation"] = self.serialization
        parameters["out_node"] = self.out_node.unique_name
        parameters["out_port"] = self.out_port.port_id
        parameters["in_node"] = self.in_node.unique_name
        parameters["in_port"] = self.in_port.port_id
        parameters["sequence_id"] = self.sequence_id
        if self.multicast_endpoint is not None:
            parameters["multicast_endpoint"] = self.multicast_endpoint.parameters()
        return parameters

    def sigma_serialize(self):
        parameters = dict()
        parameters["id"] = str(self.out_port.port_id) + "/" + str(self.in_port.port_id)
        parameters["source"] = self.out_node.unique_name
        parameters["target"] = self.in_node.unique_name

        return parameters


    @staticmethod
    def get_edge_from_parameters(parameters, workflow):
        transport = parameters["transport"]
        serialisation = parameters["serialisation"]
        sn = parameters["out_node"]
        out_port = workflow.get_port(sn, parameters["out_port"])
        rn = parameters["in_node"]
        in_port = workflow.get_port(rn, parameters["in_port"])

        multicast_endpoint = None

        if "multicast_endpoint" in parameters:
            multicast_endpoint = Endpoint.get_endpoint_from_parameters(parameters["multicast_endpoint"])

        return Edge(transport, serialisation, out_port, in_port, multicast_endpoint)

Edge.sequence_iterator = 1
