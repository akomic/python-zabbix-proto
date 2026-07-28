import json
import socket
import struct
import zlib


DEFAULT_TIMEOUT = 60


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
        except (ValueError, TypeError):
            self.data = {}


class Client:
    def __init__(self, server='127.0.0.1', port='10051', timeout=DEFAULT_TIMEOUT):
        self.server = server
        self.port = port
        self.timeout = timeout

    def __str__(self):
        return json.dumps({'server': self.server,
                           'port': self.port},
                          indent=4)

    def send(self, data):
        packetData = str(data).encode('utf-8')

        data_length = len(packetData)
        data_header = struct.pack('<Q', data_length)
        packet = b'ZBXD\x01' + data_header + packetData

        # Per-connection timeout instead of mutating the process-global default.
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(self.timeout)
        try:
            s.connect((self.server, int(self.port)))
            s.sendall(packet)

            # Read header (13 bytes: ZBXD + 1 flag byte + 8 byte length).
            header = self.__recv_exactly(s, 13)

            if len(header) < 13 or header[0:4] != b'ZBXD':
                return Response('')

            flags = header[4]
            compressed = (flags & 0x02) != 0

            if compressed:
                # Compressed: first 4 bytes = compressed size, next 4 = original size.
                datalen = struct.unpack('<I', header[5:9])[0]
            else:
                datalen = struct.unpack('<Q', header[5:13])[0]

            body = self.__recv_exactly(s, datalen)
        finally:
            s.close()

        if compressed:
            body = zlib.decompress(body)

        return Response(body.decode('utf-8'))

    @staticmethod
    def __recv_exactly(s, n):
        """Read until n bytes are received or the peer closes the connection."""
        buf = b''
        while len(buf) < n:
            chunk = s.recv(min(4096, n - len(buf)))
            if not chunk:
                break
            buf += chunk
        return buf
