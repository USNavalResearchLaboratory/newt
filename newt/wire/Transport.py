__author__ = 'Ian Taylor'

from serialize.JSON import JSON
from serialize.Pickle import Pickle
import net.Network as net
import logging
import socket
import operator
from ..Exceptions import NoDataFromEdgeException
import threading
import os

"""
The Transport class specifies the decorators for transport class implementations.
"""

lock = threading.Lock()

class Transport():

    DATA_TAG = "@DATA "

    UDP = "UDP"
    Multicast = "Multicast"
    ZMQ_TCP = "ZMQ_TCP"
    MGEN = "MGEN"
    MGENMulticast = "MGENMulticast"

    # Some serialisation mechanisms

    JSON = "JSON"
    PICKLE = "PICKLE"

    LOG_DIR = "/tmp/newt"

    serialization = PICKLE

    def __init__(self):
        #wrpcap("temp.cap",pkts)
        pass

    def init_logs(self, transport_impl):
        if not os.path.exists("/tmp"):
            os.makedirs("/tmp")
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)


    @classmethod
    def initialise_server(cls, init):
        def init_wrapper(transport_impl, target_method, bind_address, bind_port,
                         multicast_address=None, multicast_port=None):

            logger = logging.getLogger('Transport: Initialize Server')
            exc_info = None
            if bind_address == "localhost":
                bind_address = net.get_local_ip_address()
            else:
                bind_address = bind_address

            logger.debug("Init Server: Binding to address " + bind_address + " and port " + str(bind_port))

            try:
                if multicast_address is None:
                    init(transport_impl, target_method, bind_address, bind_port)
                else:
                    init(transport_impl, target_method, bind_address, bind_port, multicast_address, multicast_port)
            except socket.error as socket_error:
                import sys
                exc_info = sys.exc_info()
                print "ERROR OF TYPE: " + str(type(socket_error))     # the exception instance
                print "Details: " + str(socket_error)
                mcast_text = ""
                if multicast_address is not None:
                    mcast_text = ", Multicast Address=" + multicast_address + ", Multicast Port=" + str(multicast_port)
                print "Socket Details: Bind Address=" + bind_address + ", Bind Port=" + str(bind_port) + mcast_text
            finally:
                # Display the *original* exception
                if exc_info is not None:
                    import traceback
                    traceback.print_exception(*exc_info)
                    del exc_info
                    exit(1)

            transport_impl.bind_address = bind_address
            transport_impl.bind_port = bind_port


        return init_wrapper

    @classmethod
    def initialise_client(cls, init):
        def init_wrapper(transport_impl, bind_address, bind_port, receive_address, receive_port):
            exc_info = None
            logger = logging.getLogger('Transport: Initialize Client')

            if bind_address == "localhost":
                bind_address = net.get_local_ip_address()
            else:
                bind_address = bind_address

            if receive_address == "localhost":
                receive_address = net.get_local_ip_address()
            else:
                receive_address = receive_address

            logger.debug("Binding to address " + bind_address + " and port " + str(bind_port))

            try:
                init(transport_impl, bind_address, bind_port, receive_address, receive_port)
            except Exception as err:
                import sys
                exc_info = sys.exc_info()
                print "ERROR OF TYPE: " + str(type(err))     # the exception instance
                print "Details: " + str(err)
                send_address = ", RECEIVE/DESTINATION ADDRESS AND PORT IS NOT DEFINED FOR THIS 'OUTPUT TYPE' SOCKET"
                if receive_address is not None:
                    send_address = ", Receiver Address=" + receive_address + ", Receiver Port=" + str(receive_port)
                print "Socket Details: Bind Address=" + bind_address + ", Bind Port=" + str(bind_port) + send_address
            finally:
                # Display the *original* exception
                if exc_info is not None:
                    import traceback
                    traceback.print_exception(*exc_info)
                    del exc_info
                    exit(1)

            transport_impl.bind_address = bind_address
            transport_impl.bind_port = bind_port

        return init_wrapper

    @classmethod
    def send(cls, send_on_the_wire):
        def send_wrapper(transport_impl, *args, **kwargs):

            logger = logging.getLogger('Transport: Send')

            logger.debug("In Decorated Sender, sending " + str(args) + " " + str(kwargs) + " using " +
                         transport_impl.__class__.__name__)

            transmitter = None
            arg_list = list(args)
            for arg in arg_list:
                if arg.__class__.__name__ == "Transmitter":
                    transmitter = arg
                    arg_list.remove(arg)

            args = tuple(arg_list)

            # print "ARGS are now " + str(args)

            if Transport.serialization == Transport.JSON:
                frozen = JSON.serialize(*args, **kwargs)
            else:
                frozen = Pickle.serialize(*args, **kwargs)

            send_on_the_wire(transport_impl, frozen)

            if transmitter is not None:
                print "Starting transmitter !!!!"
                transmitter.set_send_method_details(transport_impl, send_on_the_wire, frozen)
                transmitter.start()

        return send_wrapper

    @classmethod
    def handle_message(cls, receive_method):
        def receive_wrapper(transport_impl, target_method, data, client_address):

            lock.acquire()
            workflow = None
            logger = logging.getLogger('Transport: Handle Message')
            exc_info = None
            if Transport.serialization == Transport.JSON:
                packed = JSON.deserialize(data)
            else:
                packed = Pickle.deserialize(data)

            args = packed[0]
            kwargs = packed[1]

            if hasattr(transport_impl, 'workflow'):
                workflow = transport_impl.workflow

                # Complicated ... if this method has default arguments, add these to the method but add them first
                # so that the new values can override the old ones.

            node = None
            if workflow is not None:
                node = transport_impl.workflow.get_my_node(transport_impl)
                node_name = node.unique_name

                #print "Transport receive at node " + node_name + " coming from " + client_address

                input_port = workflow.get_my_input_port(transport_impl)

                if input_port.args is not None:
                    args = [i for sub in input_port.args for i in sub]
                    #args = input_port.args + args

                if input_port.kwargs is not None:
                    kwargs= dict(Transport.combine_dictionaries(input_port.kwargs, kwargs))


            # This should have worked but I get the error:
            # TypeError: def_sensor() got multiple values for keyword argument 'mean' even though the dictionaries are
            # identical

            logger.debug("In Decorated Receiver, receiving " + str(args) + " AND " + str(kwargs) + " using " +
                         transport_impl.__class__.__name__)
            logger.debug("Sending to Method " + str(target_method))

            try:
                logger.debug("Executing method " + str(target_method) + " using:")
                logger.debug ("Args = " + str(args))
                logger.debug ("Kwargs = " + str(kwargs))

                # There is always a node for a workflow
                if node is not None:
                    return_values = target_method(node, *args, **kwargs)
                else:
                    return_values = target_method(transport_impl, *args, **kwargs)

                # Once we execute the method, we now send the data from this node's ports to the other
                # nodes it is connected to
                # Kwargs = {'mean': 2.0, 'dev': 0.5, 's_secs': 10, 'dataset': 'seismic'} worked when called
                # Kwargs = {'dataset': 'seismic', 's_secs': 10, 'dev': 0.4171342709488157, 'mean': 2.117} did not

                if workflow is not None:
                    logger.debug("Looking at which output ports need activating")

                    output_ports = node.get_output_ports()

                    for port in output_ports:
                        logger.debug("Looking at port with bind add: " + port.bind_address + ", port: " + str(port.bind_port))
                        if port.enabled is True: # is the port enabled for sending or was it disabled by the method?
                            logger.debug("Port " + str(port.port_id) + " is enabled !! ")
                            edge = workflow.get_edge_for_port(port.port_id)

                            from Adapter import Adapter
                            sender_adapter = Adapter(edge.transport, edge.serialization, workflow)
                            sender = sender_adapter.get_sender_instance(port.bind_address, port.bind_port,
                                                                        edge.get_receiver_address(),
                                                                        edge.get_receiver_port())
                            port.bind_address = sender.bind_address
                            port.bind_port = sender.bind_port

                            node = workflow.get_node_for_port(port)

                            args = port.args
                            kwargs = port.kwargs
                            Transport.parse_arguments_and_send(sender, node, return_values, *args, **kwargs)

            except Exception as inst:
                import sys
                exc_info = sys.exc_info()
                print "ERROR OF TYPE: " + str(type(inst))     # the exception instance
                print "Details: " + str(inst)
            finally:
                # Display the *original* exception
                if exc_info is not None:
                    import traceback
                    traceback.print_exception(*exc_info)
                    del exc_info

            lock.release()

        return receive_wrapper

    """
        Extracts any passed data values from the input ports and sender the data
        to the next node in the workflow.
    """

    @staticmethod
    def parse_arguments_and_send(sender, node, return_values, *args, **kwargs):
        logger = logging.getLogger('Transport')
        # print("Port Type " + str(port.port_type))
        # e.g.
        #next_method_args = list(["@DATA[1]", "@DATA[2]", "@DATA[0]"])
        #next_method_kwargs = dict({'first_name': "@DATA[last_name]", 'last_name': "@DATA[first_name]"})

        logger.debug("In argument parser for Node = " + node.unique_name)
        logger.debug("Returned args = " + str(return_values))
        logger.debug ("Args = " + str(args))
        logger.debug ("Kwargs = " + str(kwargs))

        returned_args = list()
        returned_kwargs = dict()

        if isinstance(return_values, dict):
            returned_kwargs = return_values
        elif isinstance(return_values, list):
            if return_values is not None and len(return_values) > 0:
                returned_args = return_values[0]
                returned_kwargs = return_values[1]


        logger.debug("Returned args = " + str(returned_args))
        logger.debug("Returned kwargs = " + str(returned_kwargs))

        to_pass_args = list()
        to_pass_kwargs = dict()

        i = 0

        for arg in args:
            if not isinstance( arg, ( int, long )) and arg.startswith("@DATA"):
                pos1 = operator.indexOf(arg, "[")
                pos2 = operator.indexOf(arg, "]")
                index = arg[pos1+1:pos2]
                if returned_args is None or index not in returned_args and \
                                returned_kwargs is None or index not in returned_kwargs:
                    msg = "Data for sending to " + sender.bind_address + "/" + str(sender.bind_port) + \
                          " used the @DATA tag: '" + str(arg) + "' but there is no index or dictionary value '" + \
                          str(index) + "' with this value exists in the return values of the previous method. " + \
                          "\nPossible indexes for lists items are: '" +  str(returned_args) + "'." \
                                                                                              "\nAnd possible indexes for dicts are: '" +  str(returned_kwargs) + "'. " \
                                                                                                                                                                  "Please check your workflow!"
                    raise NoDataFromEdgeException(msg)
                else:
                    if isinstance(index, int):
                        to_pass_args.append(returned_args[int(index)])
                    else:
                        to_pass_kwargs[index] = returned_kwargs[index]
            else:
                to_pass_args.append(args[i])
            i += 1

        for key, value in kwargs.iteritems():
            if not isinstance( value, ( int, long )) and value.startswith("@DATA"):
                pos1 = operator.indexOf(value, "[")
                pos2 = operator.indexOf(value, "]")
                index = value[pos1+1:pos2]
                if returned_args is None or index not in returned_args and \
                                returned_kwargs is None or index not in returned_kwargs:
                    msg = "Data for sending to " + sender.bind_address + "/" + str(sender.bind_port) + \
                          " used the @DATA tag: '" + str(value) + "' but there is no index or dictionary value '" + \
                          str(index) + "' with this value exists in the return values of the previous method. " + \
                          "\nPossible indexes for lists items are: '" +  str(returned_args) + "'." \
                                                                                              "\nAnd possible indexes for dicts are: '" +  str(returned_kwargs) + "'. " \
                                                                                                                                                                  "Please check your workflow!"
                    raise NoDataFromEdgeException(msg)
                else:
                    if isinstance(index, int):
                        to_pass_args.append(returned_args[int(index)])
                    else:
                        to_pass_kwargs[key] = returned_kwargs[index]
            else:
                to_pass_kwargs[key] = value

        logger.debug("To Pass Args = " + str(to_pass_args))
        logger.debug("To Pass Kwargs = " + str(to_pass_kwargs))

        #   exit()

        sender.send(*to_pass_args, **to_pass_kwargs)
        sender.close()

    @staticmethod
    def combine_dictionaries(kwargs_default, kwargs):
        try:
            for key, val in kwargs.items():
                kwargs_default[key] = val
        except AttributeError: # In case oth isn't a dict
            return NotImplemented # The convention when a case isn't handled

        return kwargs_default