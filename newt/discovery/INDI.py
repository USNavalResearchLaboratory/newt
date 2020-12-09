__author__ = 'scmijt'

from ..wire.Adapter import Adapter
from ..wire.Transport import Transport
from ServiceInfo import ServiceInfo
from AdvertizedServiceInfoCache import AdvertizedServiceInfoCache
from DiscoveredServiceInfoCache import DiscoveredServiceInfoCache
from ..wire.transmit.Transmitter import Transmitter

import logging
import uuid
import threading

DEFAULT_BIND_ADDRESS = "localhost"
DEFAULT_BIND_PORT_SENDER = 5354
DEFAULT_BIND_PORT_RECEIVER = 5355

DEFAULT_DISCOVERY_ADDRESS = "224.1.2.3"
DEFAULT_DISCOVERY_PORT = 5353


class INDI:
    started = False

    def __init__(self, indi_id=None, transmitter=Transmitter(), transport=Transport.Multicast, serialization=Transport.JSON):
        if indi_id is None:
            self.indi_id = str(uuid.uuid4())
        else:
            self.indi_id = indi_id
        self.transmitter = transmitter
        self.logger = self.setup_custom_logger('main')
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug('Logger Setup')

        log_format = '%(asctime)s %(message)s'

        logging.basicConfig(format=log_format)

        self.adapter = Adapter(transport, serialization)
        self.receiver = self.adapter.get_receiver_instance(self.discover_service, DEFAULT_BIND_ADDRESS, DEFAULT_BIND_PORT_RECEIVER,
                                                           DEFAULT_DISCOVERY_ADDRESS, DEFAULT_DISCOVERY_PORT)
        self.sender = self.adapter.get_sender_instance(DEFAULT_BIND_ADDRESS, DEFAULT_BIND_PORT_SENDER,
                                                       DEFAULT_DISCOVERY_ADDRESS, DEFAULT_DISCOVERY_PORT)
        # my services
        self.local_service_advert_cache = AdvertizedServiceInfoCache(self)
        # other entities services
        self.discovered_service_cache = DiscoveredServiceInfoCache(self)

        self.receiver.start()

    def setup_custom_logger(self, name):
        formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s')

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)
        logger.addHandler(handler)
        return logger

    def advertise(self, service_info):
        self.local_service_advert_cache.store(service_info)
        if not self.started:
            self.start()

    def start(self):
        t = threading.Thread(target=self.transmit)
        t.setDaemon(True) # don't hang on exit
        t.start()

    def transmit(self):
        # start sending once we have something in the cache
        all_my_adverts = self.local_service_advert_cache.get_all_as_parameters()

        self.sender.send(all_my_adverts, self.transmitter)

    def discover_service(self, transport, service_info_list):
        print self.indi_id + " Just Received New Service List"
        #        print (str(service_info_list))

        for service_id, service_info_pars in service_info_list.iteritems():
            service_info = ServiceInfo.create_using(service_info_pars)

            if service_info.is_mine(self.indi_id):
                all_my_adverts = self.local_service_advert_cache.get_all_as_parameters()
                self.transmitter.change_payload(all_my_adverts)
            else:
                self.discovered_service_cache.store(service_info)

    def close(self):
        self.transmitter.close()
        self.receiver.close()
        self.sender.close()

