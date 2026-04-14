from datetime import datetime
import json
import uuid

from zabbixproto import PROXY_VERSION, ResponseException, Client


class Proxy:
    def __init__(self, proxy_name, server_ip, server_port):
        self.proxy_name = proxy_name
        self.server_ip = server_ip
        self.server_port = server_port
        self.client = Client(self.server_ip, self.server_port)
        self.session = uuid.uuid4().hex
        self.config_revision = 0

    def send_heartbeat(self):
        packet = ProxyHeartbeatPacket(self.proxy_name)
        try:
            self.sendWithResponse(packet)
        except ResponseException:
            pass  # Heartbeat response may be empty in Zabbix 7.0

    def sendWithResponse(self, packet):
        resp = self.client.send(packet)
        if 'response' not in resp.data:
            raise ResponseException('no response')
        elif resp.data['response'] != 'success':
            if 'info' in resp.data:
                raise ResponseException("[{}]".format(resp.data['info']))
            else:
                raise ResponseException('unknown failure: {}'.format(resp))
        return (resp.data['info'] if 'info' in resp.data else '')

    def get_config(self):
        packet = ProxyConfigPacket(self.proxy_name, self.session, self.config_revision)
        resp = self.client.send(packet)

        if 'response' in resp.data and resp.data['response'] == 'failed':
            raise ResponseException(resp.data['info'])

        if 'config_revision' in resp.data:
            self.config_revision = resp.data['config_revision']

        return resp


class ProxyHeartbeatPacket:
    def __init__(self, proxy_name):
        self.proxy_name = proxy_name
        self.__reset()

    def __str__(self):
        return json.dumps(self.packet)

    def __reset(self):
        self.packet = {'request': 'proxy heartbeat',
                       'host': self.proxy_name,
                       'version': PROXY_VERSION}


class ProxyConfigPacket:
    def __init__(self, proxy_name, session, config_revision=0):
        self.proxy_name = proxy_name
        self.session = session
        self.config_revision = config_revision
        self.__reset()

    def __str__(self):
        return json.dumps(self.packet)

    def __reset(self):
        self.packet = {'request': 'proxy config',
                       'host': self.proxy_name,
                       'version': PROXY_VERSION,
                       'session': self.session,
                       'config_revision': self.config_revision}


class ProxyDataPacket:
    def __init__(self, proxy_name, session=None):
        self.proxy_name = proxy_name
        self.session = session or uuid.uuid4().hex
        self.__reset()

    def __str__(self):
        return json.dumps(self.packet)

    def add_interface_availability(self, interfaceid, available, error=''):
        if not (isinstance(available, int)) or available not in [0, 1, 2]:
            raise TypeError('available must be int 0,1,2')

        metric = {'interfaceid': int(interfaceid),
                  'available': int(available),
                  'error': error}

        if 'interface availability' not in self.packet:
            self.packet['interface availability'] = []

        self.packet['interface availability'].append(metric)

    # Backward-compatible alias
    def add_host_availability(self, hostid=None, interfaceid=None, available=0, error='',
                              snmp_available=None, snmp_error='',
                              ipmi_available=None, ipmi_error='',
                              jmx_available=None, jmx_error=''):
        iid = interfaceid if interfaceid is not None else hostid
        self.add_interface_availability(iid, available, error)

    def add_history_data(self, itemid, value="", state=0, clock=datetime.now().timestamp(), ns=0):
        if not (isinstance(clock, int)) and not (isinstance(clock, float)):
            raise TypeError('Clock must be unixtime')

        if not (isinstance(state, int)) and state not in [0, 1]:
            raise TypeError('state must be int 0,1')

        metric = {
            'itemid': str(itemid),
            'clock': int(clock),
            'ns': int(ns),
            'value': value,
            'id': len(self.packet['history data']) + 1 if 'history data' in self.packet else 1,
            'state': str(state),
        }
        if 'history data' not in self.packet:
            self.packet['history data'] = []

        self.packet['history data'].append(metric)

    def add_autoregistration(self, host, ip="127.0.0.1", dns=None, port=None, host_metadata=None, clock=datetime.now().timestamp()):
        if (isinstance(clock, int)) or (isinstance(clock, float)):
            metric = {'host': str(host),
                      'clock': int(clock),
                      'ip': str(ip)}

            if dns is not None:
                metric['dns'] = str(dns)
            if port is not None:
                metric['port'] = str(port)
            if host_metadata is not None:
                metric['host_metadata'] = str(host_metadata)
        else:
            raise TypeError('Clock must be unixtime')

        if 'auto registration' not in self.packet:
            self.packet['auto registration'] = []
        self.packet['auto registration'].append(metric)

    def data_size(self):
        size = 0
        for l in ['interface availability', 'history data', 'discovery data', 'auto registration', 'tasks']:
            if l in self.packet:
                try:
                    size += len(self.packet[l])
                except Exception:
                    pass
        return size

    def __reset(self):
        self.packet = {'request': 'proxy data',
                       'host': self.proxy_name,
                       'session': self.session,
                       'clock': int(datetime.now().timestamp()),
                       'version': PROXY_VERSION}
