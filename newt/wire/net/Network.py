__author__ = 'Ian Taylor'
"""
    Various networking utilities
"""

import socket
import os
import netifaces as ni

def is_a_local_address(address):
    if address == "localhost":
        return True

    address_list = socket.getaddrinfo(socket.gethostname(), None)

    ip_list = []
    for item in address_list:
        if item[4][0] == address:
            return True

    return False


def verify_and_get_address(hostname):
    ip = str(socket.gethostbyname(hostname))
    if str(ip).startswith("127.") and os.name != "nt":
        interfaces = ni.interfaces()
        for ifname in interfaces:
            try:
                inter = ni.ifaddresses(ifname)
                if inter is not None:
#                    for item in inter:
 #                       print "Item " + str(item)

                    if len(inter) > 2:
                        ip = inter[2][0]['addr']

                    if ip.startswith("127."):
                        pass
                    else:
                        break
            except IOError as e:
                pass

#        print "Local IP is " + ip

    return ip


def get_local_ip_address():
    if get_local_ip_address.host_address is not None:
        return get_local_ip_address.host_address

    host_address_det = None

    if socket.gethostname().find('.')>=0:
        hostname=socket.gethostname()
    else:
        hostname=socket.gethostbyaddr(socket.gethostname())[0]

    if hostname.startswith("1.0.0.0.0.0"):
        return "127.0.0.1"
    try:
        host_address_det = verify_and_get_address(hostname)
    except IOError as e:
        print "Using the system HOSTNAME variable: " + hostname + " does not resolve using nslookup. Trying to get localhost using adapters instead ..."
        hostname = [(s.connect(('8.8.8.8', 80)), s.getsockname()[0], s.close()) for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
        try:
            host_address_det = verify_and_get_address(hostname)
        except IOError as e:
            print "Tried connection method and failed too !! I must fall on my sword ..."
            exit()

    get_local_ip_address.host_address = host_address_det

    return get_local_ip_address.host_address


get_local_ip_address.host_address = None


def is_valid_ipv4_address(address):
    try:
        socket.inet_pton(socket.AF_INET, address)
    except AttributeError:  # no inet_pton here, sorry
        try:
            socket.inet_aton(address)
        except socket.error:
            return False
        return address.count('.') == 3
    except socket.error:  # not a valid address
        return False

    return True


def is_valid_ipv6_address(address):
    try:
        socket.inet_pton(socket.AF_INET6, address)
    except socket.error:  # not a valid address
        return False
    return True


def is_valid_ip(ip):
    """Validates IP addresses.
    """
    return is_valid_ipv4_address(ip) or is_valid_ipv6_address(ip)


def get_interface_ip(ifname):
    return ni.ifaddresses(ifname)[2][0]['addr']

def get_ip_address_for(address_or_interface):
    if address_or_interface == "localhost":
        address_or_interface = get_local_ip_address()

    if is_valid_ip(address_or_interface):
        addr = address_or_interface
    else:
        addr = get_interface_ip(address_or_interface)

    if addr is None:
        raise Exception("Address " +  address_or_interface +
            " is not an IP nor is it a network interface. You must use a valid IP address, please check your settings.")

    return addr

def get_rpc_endpoint_for(address_or_interface, bind_port):

    addr = get_ip_address_for(address_or_interface)

    return "tcp://"+addr+":"+str(bind_port)