__author__ = 'scmijt'

import json
from SerializeInterface import SerializeInterface

"""
    An interface to be implemented by all serialization methods.
"""


class JSON(SerializeInterface):

    @staticmethod
    def serialize(*args, **kwargs):
        return json.dumps((args, kwargs))

    @staticmethod
    def serialize_dic(dictionary, prettify=False):
        if prettify:
            return json.dumps(dictionary, indent=4, sort_keys=True)
        else:
            return json.dumps(dictionary)

    @staticmethod
    def deserialize(data):
        return JSON.byteify(json.loads(data))

    # helper methods.

    @staticmethod
    def byteify(input):
        if isinstance(input, dict):
            return {JSON.byteify(key):JSON.byteify(value) for key,value in input.iteritems()}
        elif isinstance(input, list):
            return [JSON.byteify(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input
