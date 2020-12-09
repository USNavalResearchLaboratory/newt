__author__ = 'scmijt'

import logging

"""
A cache for storing the service adverts, checking synchronization and expiring them when they timeout.
"""


class ServiceInfoCache:

    cache = None

    def __init__(self, indi):
        self.logging = logging.getLogger('main')

        self.cache = dict()
        self.reaper = CacheReaper(self)
        self.indi = indi

    def store(self, service_info):
        self.reaper.prune()
        if not self.contains(service_info.service_id):
            self.cache[service_info.service_id] = service_info
            print "Saving advert to the " + self.__class__.__name__ + "!!"
            logging.debug(self.__class__.__name__ + " Discovered Object " + service_info.to_string())
            return True
        return False

    def retrieve(self, service_id):
        if self.contains(service_id):
            return self.cache[service_id]
        else:
            return None

    def contains(self, service_id):
        return service_id in self.cache

    def retrieve_all(self):
        self.reaper.prune()
        return self.cache.values()

    def retrieve_all_as_dict(self):
        self.reaper.prune()
        return self.cache

    def get_all_as_parameters(self):
        services = dict()
        for service_id, service_info in self.cache.iteritems():
            services[service_id] = service_info.to_parameters()
        return services

    def remove(self, service_id):
        return self.cache.pop(service_id)

    def synchronize_cache(self):
        self.reaper.prune()


class CacheReaper:
    def __init__(self, service_info_cache):
        self.service_info_cache = service_info_cache

    def prune(self):
        for service_id, service_info in self.service_info_cache.cache.iteritems():
            if service_info.is_expired():
                self.service_info_cache.remove(service_id)

