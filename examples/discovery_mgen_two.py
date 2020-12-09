__author__ = 'scmijt'

from newt.discovery.ServiceInfo import ServiceInfo
from newt.discovery.INDI import INDI
from newt.wire.Transport import Transport


indi = INDI("INDI MGEN 2", None, Transport.MGEN)

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
