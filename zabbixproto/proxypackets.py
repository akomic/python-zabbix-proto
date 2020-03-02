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

        self.sendWithResponse(packet)

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
        packet = ProxyConfigPacket(self.proxy_name)

        resp = self.client.send(packet)

        if 'response' in resp.data and resp.data['response'] == 'failed':
            raise ResponseException(resp.data['info'])

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


class ProxyHostavailabilityPacket:
    # This is for version 3.2.X only

    def __init__(self, proxy_name):
        self.proxy_name = proxy_name
        self.clean()

    def __str__(self):
        return json.dumps(self.packet)

    def add(self, hostid, available, error='', snmp_available=None, snmp_error='', ipmi_available=None, ipmi_error='', jmx_available=None, jmx_error=''):
        # 	available	number	Zabbix agent availability

        # 0, HOST_AVAILABLE_UNKNOWN - unknown
        # 1, HOST_AVAILABLE_TRUE - available
        # 2, HOST_AVAILABLE_FALSE - unavailable
        # error	string	Zabbix agent error message or empty string
        # snmp_available	number	SNMP agent availability

        # 0, HOST_AVAILABLE_UNKNOWN - unknown
        # 1, HOST_AVAILABLE_TRUE - available
        # 2, HOST_AVAILABLE_FALSE - unavailable
        # snmp_error	string	SNMP agent error message or empty string
        # ipmi_available	number	IPMI agent availability

        # 0, HOST_AVAILABLE_UNKNOWN - unknown
        # 1, HOST_AVAILABLE_TRUE - available
        # 2, HOST_AVAILABLE_FALSE - unavailable
        # ipmi_error	string	IPMI agent error message or empty string
        # jmx_available	number	JMX agent availability

        # 0, HOST_AVAILABLE_UNKNOWN - unknown
        # 1, HOST_AVAILABLE_TRUE - available
        # 2, HOST_AVAILABLE_FALSE - unavailable
        # jmx_error	string	JMX agent error message or empty string

        if not (isinstance(available, int)) or available not in [0, 1, 2]:
            raise TypeError('available must be int 0,1,2')
        if snmp_available is not None and (not (isinstance(snmp_available, int)) or snmp_available not in [0, 1, 2]):
            raise TypeError('snmp_available must be int 0,1,2')
        if ipmi_available is not None and (not (isinstance(ipmi_available, int)) or ipmi_available not in [0, 1, 2]):
            raise TypeError('ipmi_available must be int 0,1,2')
        if jmx_available is not None and (not (isinstance(available, int)) or jmx_available not in [0, 1, 2]):
            raise TypeError('jmx_available must be int 0,1,2')

        metric = {'hostid': int(hostid),
                  'available': int(available)}

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

        self.packet['data'].append(metric)

    def clean(self):
        self.packet = {'request': 'host availability',
                       'host': self.proxy_name,
                       'data': []}


class ProxyHistorydataPacket:
    # This is for version 3.2.X only
    def __init__(self, proxy_name):
        self.proxy_name = proxy_name
        self.clean()

    def __str__(self):
        return json.dumps(self.packet)

    def add(self, host, key, value, state=0, clock=datetime.now().timestamp()):
        # state
        # 0, ITEM_STATE_NORMAL
        # 1, ITEM_STATE_NOTSUPPORTED
        if not (isinstance(clock, int)) and not (isinstance(clock, float)):
            raise TypeError('Clock must be unixtime')

        if not (isinstance(state, int)) and state not in [0, 1]:
            raise TypeError('state must be int 0,1')

        metric = {'host': str(host),
                  'key': str(key),
                  'state': int(state),
                  'value': str(value),
                  'clock': int(clock)}

        self.packet['data'].append(metric)

    def clean(self):
        self.packet = {'request': 'history data',
                       'host': self.proxy_name,
                       'data': [],
                       'clock': datetime.now().timestamp()}
