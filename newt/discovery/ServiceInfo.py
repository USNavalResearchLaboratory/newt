__author__ = 'scmijt'

import datetime
import time
import uuid


class ServiceInfo(object):
    # housekeeping
    service_id=-1
    time_created=0
    creator_id=None
    # naming
    service_name=""
    scope=""

    # URL
    protocol="http"
    address="localhost"
    port=None
    resource_path="/"

    #timeout of advert - relative to time_created
    timeout=-1

    def __init__(self, indi_id):
        self.time_created = int(time.time())
        self.service_id = str(uuid.uuid4())
        self.creator_id = indi_id

    def to_string(self):
        time_formatted = datetime.datetime.fromtimestamp(self.time_created).strftime('%Y-%m-%d %H:%M:%S')

        return "Service Name = " + self.service_name + ", " +\
               "Service ID = " +str(self.service_id) + "," +\
               "Time Created: " + time_formatted + "," +\
               "URL = " +  self.get_endpoint() + ", " +\
               "Timeout = " +  str(self.timeout) + ", " +\
               "Scope = " +  self.scope + ","

    def get_endpoint(self):
        protocol = ""

        if self.port is not None:
            return protocol + "://" + self.address + ":" + str(self.port) + "/" + self.resource_path
        else:
            return protocol + "://" + self.address + "/" + self.resource_path

    def is_mine(self, indi_id):
        return indi_id == self.creator_id

    def to_parameters(self):
        parameters = dict()
        parameters['creator_id'] = self.creator_id
        parameters['service_id'] = self.service_id
        parameters['time_created'] = self.time_created
        parameters['service_name'] = self.service_name
        parameters['scope'] = self.scope

        parameters['protocol'] = self.protocol
        parameters['address'] = self.address

        parameters['port'] = self.port
        parameters['port'] = self.port

        parameters['resource_path'] = self.resource_path

        ServiceInfo.serialization_count+=1

        parameters['serialization_count'] = ServiceInfo.serialization_count

        return parameters

    @staticmethod
    def create_using(parameters):
        creator_id = parameters['creator_id']
        service_info = ServiceInfo(creator_id)
        service_info.service_id = parameters['service_id']
        service_info.time_created= parameters['time_created']
        service_info.service_name= parameters['service_name']
        service_info.scope= parameters['scope']

        service_info.protocol= parameters['protocol']
        service_info.address= parameters['address']

        service_info.address= parameters['address']

        if "port" in parameters:
            service_info.port = parameters['port']

        if "resource_path" in parameters:
            service_info.resource_path = parameters['resource_path']

        return service_info

    def is_expired(self):

        max_limit = self.timeout

        if max_limit == -1:
            return False

        time_now = int(time.time())

        if (time_now-self.time_created) > max_limit:
            return True
        else:
            return False

    # house keeping, on creation and deletion

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # remove this avdert from cache when deleted.
        if hasattr(ServiceInfo, 'my_services'):
            ServiceInfo.my_services.pop(self.service_id)

    # comparisons
    def __cmp__(self, other):
        return self.__eq__(other)

    def __eq__(self, other):
        if self.service_id == other.service_id:
            return True
        else:
            return False

    def __lt__(self, other):
        return self.service_name < other.service_name

    def __le__(self, other):
        return self.service_name <= other.service_name

    def __ne__(self, other):
        return self.service_name != other.service_name

    def __gt__(self, other):
        return self.service_name > other.service_name

    def __ge__(self, other):
        return self.service_name >= other.service_name

ServiceInfo.serialization_count = 1
