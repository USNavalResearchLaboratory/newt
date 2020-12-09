from __future__ import generators

__author__ = 'scmijt'

from abc import abstractmethod


class SerializeInterface:
    
    def __init__(self):
        pass

    @abstractmethod
    def serialize(*args, **kwargs):
        pass

    @abstractmethod
    def deserialize(data):
        pass
