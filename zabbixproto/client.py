import json
import socket
import time
import struct


class Response:
    def __init__(self, json):
        self.json = json
        self.data = {}
        self.__parse()

    def __str__(self):
        return self.json

    def __getitem__(self, item):
        return self.data[item]

    def __parse(self):
        try:
            self.data = json.loads(self.json)
        except:
            self.data = {}
            pass


class Client:
    def __init__(self, server='127.0.0.1', port='10051'):
        self.server = server
        self.port = port

    def __str__(self):
        return json.dumps({'server': self.server,
                           'port': self.port},
                          indent=4)

    def send(self, data):
        packetData = str(data).encode('utf-8')
        socket.setdefaulttimeout(60)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        s.connect((self.server, int(self.port)))

        data_length = len(packetData)
        data_header = struct.pack('<Q', data_length)
        packet = bytes('ZBXD\1', 'utf-8') + data_header + packetData

        s.sendall(packet)
        time.sleep(0.5)

        datalen = None
        body = b''
        idx = 0
        while True:
            idx += 1
            if datalen is not None and len(body) >= datalen:
                break

            data = s.recv(1024)

            if len(data) == 0 and idx >= 5:
                break

            if datalen is None and data[0:5] == b'ZBXD\1':
                datalen = struct.unpack('<Q', data[5:13])[0]
                body = data[13:]
            else:
                body += data

        resp = Response(body.decode('utf-8'))
        s.close()
        return resp
