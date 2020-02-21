from datetime import datetime
import json

from zabbixproto import PROXY_VERSION, ResponseException, Client


class Proxy:
    def __init__(self, proxy_name, server_ip, server_port):
        self.proxy_name = proxy_name
        self.server_ip = server_ip
        self.server_port = server_port
        self.client = Client(self.server_ip, self.server_port)

    def send_heartbeat(self):
        packet = ProxyHeartbeatPacket(self.proxy_name)

        resp = self.client.send(packet)
        if 'response' in resp.data and resp.data['response'] == 'success':
            return True, ''
        else:
            msg = 'no response'
            if 'info' in resp.data:
                msg = resp.data['info']
            return False, msg

    def send_auto_registration(self, packet):
        resp = self.client.send(packet)
        if 'response' not in resp.data:
            raise ResponseException('no response')
        elif resp.data['response'] != 'success':
            if 'info' in resp.data:
                raise ResponseException(resp.data['info'])
            else:
                raise ResponseException('unknown failure: {}'.format(resp))
        return

    def get_config(self):
        packet = ProxyConfigPacket(self.proxy_name)

        resp = self.client.send(packet)

        return resp


class ProxyHeartbeatPacket:
    def __init__(self, proxy_name):
        self.proxy_name = proxy_name
        self.clean()

    def __str__(self):
        return json.dumps(self.packet)

    def clean(self):
        self.packet = {'request': 'proxy heartbeat',
                       'host': self.proxy_name,
                       'version': PROXY_VERSION}


class ProxyConfigPacket:
    def __init__(self, proxy_name):
        self.proxy_name = proxy_name
        self.clean()

    def __str__(self):
        return json.dumps(self.packet)

    def clean(self):
        self.packet = {'request': 'proxy config',
                       'host': self.proxy_name,
                       'version': PROXY_VERSION}


class ProxyDataPacket:
    # This is for version 3.4.X only
    def __init__(self, proxy_name):
        self.proxy_name = proxy_name
        self.clean()

    def __str__(self):
        return json.dumps(self.packet)

    def add_auto_registration(self, host, ip=None, dns=None, port=None, host_metadata=None, clock=datetime.now().timestamp()):
        if (isinstance(clock, int)) or (isinstance(clock, float)):
            metric = {'host': str(host),
                      'clock': int(clock)}

            if ip is not None:
                metric['ip'] = str(ip)
            if dns is not None:
                metric['dns'] = str(dns)
            if port is not None:
                metric['port'] = str(port)
            if host_metadata is not None:
                metric['host_metadata'] = str(host_metadata)
        else:
            raise TypeError('Clock must be unixtime')

        self.packet['auto registration'].append(metric)

    def clean(self):
        self.packet = {'request': 'proxy data',
                       'host': self.proxy_name,
                       'host availability': [],
                       'history data': [],
                       'discovery data': [],
                       'auto registration': [],
                       'tasks': [],
                       'version': PROXY_VERSION}


class ProxyAutoregistrationPacket:
    # This is for version 3.2.X only

    def __init__(self, proxy_name):
        self.proxy_name = proxy_name
        self.clean()

    def __str__(self):
        return json.dumps(self.packet)

    def add(self, host, ip=None, dns=None, port=None, host_metadata=None, clock=datetime.now().timestamp()):
        if (isinstance(clock, int)) or (isinstance(clock, float)):
            metric = {'host': str(host),
                      'clock': int(clock)}

            if ip is not None:
                metric['ip'] = str(ip)
            if dns is not None:
                metric['dns'] = str(dns)
            if port is not None:
                metric['port'] = str(port)
            if host_metadata is not None:
                metric['host_metadata'] = str(host_metadata)
        else:
            raise TypeError('Clock must be unixtime')

        self.packet['data'].append(metric)

    def clean(self):
        self.packet = {'request': 'auto registration',
                       'host': self.proxy_name,
                       'data': [],
                       'clock': datetime.now().timestamp()}
