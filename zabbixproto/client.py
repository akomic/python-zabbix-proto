import json
import socket
import time
import struct
import zlib


class Response:
    def __init__(self, json_str):
        self.json = json_str
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
        packet = b'ZBXD\x01' + data_header + packetData

        s.sendall(packet)
        time.sleep(0.5)

        # Read header (13 bytes minimum: ZBXD + flags + 8 byte length)
        header = b''
        while len(header) < 13:
            chunk = s.recv(13 - len(header))
            if not chunk:
                break
            header += chunk

        if len(header) < 13 or header[0:4] != b'ZBXD':
            s.close()
            return Response('')

        flags = header[4]
        compressed = (flags & 0x02) != 0

        if compressed:
            # Compressed: first 4 bytes of length = compressed size, next 4 = original size
            compressed_len = struct.unpack('<I', header[5:9])[0]
            original_len = struct.unpack('<I', header[9:13])[0]
            datalen = compressed_len
        else:
            datalen = struct.unpack('<Q', header[5:13])[0]

        # Read body
        body = b''
        while len(body) < datalen:
            chunk = s.recv(min(4096, datalen - len(body)))
            if not chunk:
                break
            body += chunk

        s.close()

        if compressed:
            body = zlib.decompress(body)

        return Response(body.decode('utf-8'))
