__author__ = 'scmijt'


from ServiceInfoCache import ServiceInfoCache
import logging

"""
A cache for storing discovered service infos for this client. Discovered service infos
come from distributed publishers. A node does not store it's own services in this cache.
It also checks and expires them when they timeout.
"""


class DiscoveredServiceInfoCache(ServiceInfoCache):
    def __init__(self, indi):
        ServiceInfoCache.__init__(self, indi)

    def store(self, service_info):
        self.reaper.prune()
        if not self.contains(service_info.service_id) and not service_info.is_mine(self.indi.indi_id):
            self.cache[service_info.service_id] = service_info
            self.logging.debug(self.__class__.__name__ + " Discovered Object " + service_info.to_string())
            return True
        return False

