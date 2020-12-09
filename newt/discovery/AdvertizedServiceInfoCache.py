__author__ = 'scmijt'


from ServiceInfoCache import ServiceInfoCache

"""
A cache for storing advertized service infos from this client. It also checks and expires them
when they timeout.
"""


class AdvertizedServiceInfoCache(ServiceInfoCache):
    def __init__(self, indi):
        ServiceInfoCache.__init__(self, indi)