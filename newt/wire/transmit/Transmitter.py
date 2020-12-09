from __future__ import generators
from abc import abstractmethod
import time
import threading

from ..Transport import Transport
from ..serialize.JSON import JSON
from ..serialize.Pickle import Pickle

__author__ = 'scmijt'


class TransmitterAlgorithm:
    def __init__(self):
        pass

    """
    Returns the number of seconds to the next transmission
    """
    @abstractmethod
    def get_next_time_period(self):
        return None

    """
    Returns the maximum time limit to transmit - provides a cut off for transmitting
    """
    @abstractmethod
    def get_max_time_limit(self):
        return None


class FixedIntervalTransmitter(TransmitterAlgorithm):
    interval=None
    max_time=None

    def __init__(self, interval=1, max_time=-1):
        TransmitterAlgorithm.__init__(self)
        self.interval=interval
        self.max_time = max_time

    def get_next_time_period(self):
        return self.interval

    def get_max_time_limit(self):
        return self.max_time


"""
    Simple class to return the temporal sequence that a transmitter should transmit against.
    Transmitters are pluggable and the default one uses a fixed interval for retransmitting
    the packet
"""


class Transmitter:
    algorithm = None
    start_time=None

    def __init__(self, algorithm=FixedIntervalTransmitter()):
        self.algorithm=algorithm
        self.transport_impl = None
        self.send_method = None
        self.payload = None
        self.running = False


    def get_next_time_period(self):
        if self.start_time is None:
            self.start_time = int(time.time())

        return self.algorithm.get_next_time_period()

    def has_reached_time_limit(self):
        max_limit = self.algorithm.get_max_time_limit()

        if max_limit == -1:
            return False

        time_now = int(time.time())

        if (time_now-self.start_time) > max_limit:
            return True
        else:
            return False

    def set_send_method_details(self, transport_impl, send_method, payload):
        self.transport_impl = transport_impl
        self.send_method = send_method
        self.payload = payload
        self.running = True

    def change_payload(self, *args, **kwargs):
        if Transport.serialization == Transport.JSON:
            frozen = JSON.serialize(*args, **kwargs)
        else:
            frozen = Pickle.serialize(*args, **kwargs)

        self.payload = frozen


    def start(self):
        t = threading.Thread(target=self.transmit)
        t.setDaemon(True) # don't hang on exit
        t.start()

    def transmit(self):
        while not self.has_reached_time_limit() and self.running:
            time.sleep(self.get_next_time_period())
            self.send_method(self.transport_impl, self.payload)

    def close(self):
        self.running = False