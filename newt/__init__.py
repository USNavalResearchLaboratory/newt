
"""
NEWT is a lightweight decentralised workflow tool
"""

try:
    from newt.wire.Transport import Transport
except ImportError:

    pass

VERSION = (0, 0, 1)

__version__ = '.'.join((str(each) for each in VERSION[:4]))


def get_version():
    """
    Returns shorter version (digit parts only) as string.
    """
    return '.'.join((str(each) for each in VERSION[:4]))