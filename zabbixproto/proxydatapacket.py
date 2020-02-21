from datetime import datetime
import json

# from zabbixproto import PROXY_VERSION


class ProxyHistorydataPacket:
    def __init__(self, proxy_name):
        self.proxy_name = proxy_name
        self.clean()

    def __str__(self):
        return json.dumps(self.packet)

    def add(self, host, key, value, clock=datetime.now().timestamp()):
        if (isinstance(clock, int)) or (isinstance(clock, float)):
            metric = {'host': str(host),
                      'key': str(key),
                      'value': str(value),
                      'clock': int(clock)}
        else:
            raise TypeError('Clock must be unixtime')

        self.packet['data'].append(metric)

    def clean(self):
        self.packet = {'request': 'history data',
                       'host': self.proxy_name,
                       'data': []}
