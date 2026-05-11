from datetime import datetime
import json

from zabbixproto.config import ResponseException
from zabbixproto.client import Client


class Sender:
    def __init__(self, server_ip, server_port):
        self.server_ip = server_ip
        self.server_port = server_port
        self.client = Client(self.server_ip, self.server_port)

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


class SenderDataPacket:
    def __init__(self, clock=None):
        self.packet = {
            'request': 'sender data',
            'data': [],
            'clock': int(datetime.now().timestamp()) if clock is None else int(clock)
        }

    def __str__(self):
        return json.dumps(self.packet)

    def add(self, host, key, value):
        self.packet['data'].append({
            "host": host,
            "key": key,
            "value": value
        })
