__author__ = 'scmijt'

from newt.discovery.ServiceInfo import ServiceInfo
from newt.discovery.INDI import INDI
import time
from newt.wire.transmit.Transmitter import TransmitterAlgorithm, Transmitter
import random

class RandonIntervalTransmitter(TransmitterAlgorithm):
    interval_boundary=None
    max_time=None

    def __init__(self, interval_boundary=10, max_time=-1):
        TransmitterAlgorithm.__init__(self)
        self.interval_boundary=interval_boundary
        self.max_time = max_time
        self.iteration_number =1

    def get_next_time_period(self):
        self.iteration_number +=1
        new_interval = random.randint(1, self.interval_boundary)
        print "Iteration " + str(self.iteration_number) + " using Interval " + str(new_interval)
        return new_interval


    def get_max_time_limit(self):
        return self.max_time


indi = INDI("INDI Peer 2", Transmitter(RandonIntervalTransmitter()))

meta_data = dict()
meta_data['alpha'] = 1.0
meta_data['beta'] = 99.0

service_info = ServiceInfo(indi.indi_id)
service_info.protocol="http"
service_info.address="127.0.0.1"
service_info.path="/my/path"
service_info.service_name="New service #2"

try:
    indi.advertise(service_info)
    input("Press a key to close...")
except KeyboardInterrupt:
    indi.close()
