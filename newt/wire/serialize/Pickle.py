__author__ = 'scmijt'

import pickle
from SerializeInterface import SerializeInterface

"""
    An interface to be implemented by all serialization methods.
"""


class Pickle(SerializeInterface):

    @staticmethod
    def serialize(*args, **kwargs):
       # print "Using Pickle !!!"
        return pickle.dumps((args, kwargs))


    @staticmethod
    def deserialize(data):
       # print "Using pickle to deserialise data !!!"
        return pickle.loads(data)

