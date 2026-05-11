from datetime import datetime
import json
import uuid

from zabbixproto.config import DEFAULT_PROTOCOL_VERSION, ResponseException, is_v7
from zabbixproto.client import Client


def _normalize_version(version):
    """Normalize to major.0.0 since protocol only changes at major boundaries."""
    try:
        major = int(version.split('.')[0])
        return "{}.0.0".format(major)
    except (ValueError, IndexError):
        return DEFAULT_PROTOCOL_VERSION


class Proxy:
    def __init__(self, proxy_name, server_ip, server_port, protocol_version=None):
        self.proxy_name = proxy_name
        self.server_ip = server_ip
        self.server_port = server_port
        self.protocol_version = _normalize_version(protocol_version or DEFAULT_PROTOCOL_VERSION)
        self.client = Client(self.server_ip, self.server_port)
        self.session = uuid.uuid4().hex if is_v7(self.protocol_version) else None
        self.config_revision = 0

    def send_heartbeat(self):
        packet = ProxyHeartbeatPacket(self.proxy_name, self.protocol_version)
        try:
            self.sendWithResponse(packet)
        except ResponseException:
            pass

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
        packet = ProxyConfigPacket(self.proxy_name, self.protocol_version,
                                   self.session, self.config_revision)
        resp = self.client.send(packet)

        if 'response' in resp.data and resp.data['response'] == 'failed':
            raise ResponseException(resp.data['info'])

        if is_v7(self.protocol_version) and 'config_revision' in resp.data:
            self.config_revision = resp.data['config_revision']

        return resp


class ProxyHeartbeatPacket:
    def __init__(self, proxy_name, protocol_version=None):
        self.proxy_name = proxy_name
        self.protocol_version = _normalize_version(protocol_version or DEFAULT_PROTOCOL_VERSION)
        self.__reset()

    def __str__(self):
        return json.dumps(self.packet)

    def __reset(self):
        self.packet = {'request': 'proxy heartbeat',
                       'host': self.proxy_name,
                       'version': self.protocol_version}


class ProxyConfigPacket:
    def __init__(self, proxy_name, protocol_version=None, session=None, config_revision=0):
        self.proxy_name = proxy_name
        self.protocol_version = _normalize_version(protocol_version or DEFAULT_PROTOCOL_VERSION)
        self.session = session
        self.config_revision = config_revision
        self.__reset()

    def __str__(self):
        return json.dumps(self.packet)

    def __reset(self):
        self.packet = {'request': 'proxy config',
                       'host': self.proxy_name,
                       'version': self.protocol_version}
        if is_v7(self.protocol_version) and self.session:
            self.packet['session'] = self.session
            self.packet['config_revision'] = self.config_revision


class ProxyDataPacket:
    def __init__(self, proxy_name, session=None, protocol_version=None):
        self.proxy_name = proxy_name
        self.protocol_version = _normalize_version(protocol_version or DEFAULT_PROTOCOL_VERSION)
        self.session = session or (uuid.uuid4().hex if is_v7(self.protocol_version) else None)
        self.__reset()

    def __str__(self):
        return json.dumps(self.packet)

    def add_interface_availability(self, interfaceid, available, error=''):
        if not (isinstance(available, int)) or available not in [0, 1, 2]:
            raise TypeError('available must be int 0,1,2')

        if is_v7(self.protocol_version):
            key = 'interface availability'
            metric = {'interfaceid': int(interfaceid), 'available': int(available), 'error': error}
        else:
            key = 'host availability'
            metric = {'hostid': int(interfaceid), 'available': int(available), 'error': error}

        if key not in self.packet:
            self.packet[key] = []
        self.packet[key].append(metric)

    def add_host_availability(self, hostid=None, interfaceid=None, available=0, error='',
                              snmp_available=None, snmp_error='',
                              ipmi_available=None, ipmi_error='',
                              jmx_available=None, jmx_error=''):
        if is_v7(self.protocol_version):
            iid = interfaceid if interfaceid is not None else hostid
            self.add_interface_availability(iid, available, error)
        else:
            if not (isinstance(available, int)) or available not in [0, 1, 2]:
                raise TypeError('available must be int 0,1,2')
            if snmp_available is not None and (not isinstance(snmp_available, int) or snmp_available not in [0, 1, 2]):
                raise TypeError('snmp_available must be int 0,1,2')
            if ipmi_available is not None and (not isinstance(ipmi_available, int) or ipmi_available not in [0, 1, 2]):
                raise TypeError('ipmi_available must be int 0,1,2')
            if jmx_available is not None and (not isinstance(jmx_available, int) or jmx_available not in [0, 1, 2]):
                raise TypeError('jmx_available must be int 0,1,2')
            metric = {'hostid': int(hostid), 'available': int(available), 'error': error}
            if snmp_available is not None:
                metric['snmp_available'] = int(snmp_available)
                if snmp_available == 2:
                    metric['snmp_error'] = str(snmp_error)
            if ipmi_available is not None:
                metric['ipmi_available'] = int(ipmi_available)
                if ipmi_available == 2:
                    metric['ipmi_error'] = str(ipmi_error)
            if jmx_available is not None:
                metric['jmx_available'] = int(jmx_available)
                if jmx_available == 2:
                    metric['jmx_error'] = str(jmx_error)
            if 'host availability' not in self.packet:
                self.packet['host availability'] = []
            self.packet['host availability'].append(metric)

    def add_history_data(self, itemid, value="", state=0, clock=None, ns=0):
        if clock is None:
            clock = datetime.now().timestamp()
        if not (isinstance(clock, int)) and not (isinstance(clock, float)):
            raise TypeError('Clock must be unixtime')
        if not (isinstance(state, int)) or state not in [0, 1]:
            raise TypeError('state must be int 0,1')

        metric = {
            'itemid': str(itemid),
            'clock': int(clock),
            'value': value,
            'id': len(self.packet.get('history data', [])) + 1,
            'state': str(state),
        }
        if is_v7(self.protocol_version):
            metric['ns'] = int(ns)

        if 'history data' not in self.packet:
            self.packet['history data'] = []
        self.packet['history data'].append(metric)

    def add_autoregistration(self, host, ip="127.0.0.1", dns=None, port=None,
                             host_metadata=None, clock=None):
        if clock is None:
            clock = datetime.now().timestamp()
        if not (isinstance(clock, int)) and not (isinstance(clock, float)):
            raise TypeError('Clock must be unixtime')

        metric = {'host': str(host), 'clock': int(clock), 'ip': str(ip)}
        if dns is not None:
            metric['dns'] = str(dns)
        if port is not None:
            metric['port'] = str(port)
        if host_metadata is not None:
            metric['host_metadata'] = str(host_metadata)

        if 'auto registration' not in self.packet:
            self.packet['auto registration'] = []
        self.packet['auto registration'].append(metric)

    def data_size(self):
        size = 0
        for key in ['host availability', 'interface availability', 'history data',
                    'discovery data', 'auto registration', 'tasks']:
            if key in self.packet:
                try:
                    size += len(self.packet[key])
                except Exception:
                    pass
        return size

    def __reset(self):
        self.packet = {'request': 'proxy data',
                       'host': self.proxy_name,
                       'clock': int(datetime.now().timestamp()),
                       'version': self.protocol_version}
        if is_v7(self.protocol_version) and self.session:
            self.packet['session'] = self.session
