import json
import unittest
from zabbixproto import PROXY_VERSION
from zabbixproto.proxypackets import (
    Proxy, ProxyHeartbeatPacket, ProxyConfigPacket, ProxyDataPacket
)
from zabbixproto.senderpackets import SenderDataPacket


class TestProxyVersion(unittest.TestCase):
    def test_version_is_7(self):
        self.assertEqual(PROXY_VERSION, "7.0.0")


class TestProxyHeartbeat(unittest.TestCase):
    def test_packet_structure(self):
        pkt = ProxyHeartbeatPacket("testproxy")
        data = json.loads(str(pkt))
        self.assertEqual(data['request'], 'proxy heartbeat')
        self.assertEqual(data['host'], 'testproxy')
        self.assertEqual(data['version'], '7.0.0')


class TestProxyConfigPacket(unittest.TestCase):
    def test_packet_has_session_and_revision(self):
        pkt = ProxyConfigPacket("testproxy", "abc123", 5)
        data = json.loads(str(pkt))
        self.assertEqual(data['request'], 'proxy config')
        self.assertEqual(data['host'], 'testproxy')
        self.assertEqual(data['version'], '7.0.0')
        self.assertEqual(data['session'], 'abc123')
        self.assertEqual(data['config_revision'], 5)


class TestProxyDataPacket(unittest.TestCase):
    def test_packet_has_session(self):
        pkt = ProxyDataPacket("testproxy", session="sess123")
        data = json.loads(str(pkt))
        self.assertEqual(data['request'], 'proxy data')
        self.assertEqual(data['host'], 'testproxy')
        self.assertEqual(data['session'], 'sess123')
        self.assertEqual(data['version'], '7.0.0')
        self.assertIn('clock', data)

    def test_auto_generates_session(self):
        pkt = ProxyDataPacket("testproxy")
        data = json.loads(str(pkt))
        self.assertEqual(len(data['session']), 32)

    def test_interface_availability(self):
        pkt = ProxyDataPacket("testproxy")
        pkt.add_interface_availability(interfaceid=42, available=1, error='')
        data = json.loads(str(pkt))
        self.assertIn('interface availability', data)
        self.assertEqual(len(data['interface availability']), 1)
        self.assertEqual(data['interface availability'][0]['interfaceid'], 42)
        self.assertEqual(data['interface availability'][0]['available'], 1)

    def test_host_availability_alias_uses_interfaceid(self):
        pkt = ProxyDataPacket("testproxy")
        pkt.add_host_availability(hostid=10, interfaceid=42, available=2, error='down')
        data = json.loads(str(pkt))
        self.assertEqual(data['interface availability'][0]['interfaceid'], 42)

    def test_host_availability_alias_falls_back_to_hostid(self):
        pkt = ProxyDataPacket("testproxy")
        pkt.add_host_availability(hostid=10, available=1)
        data = json.loads(str(pkt))
        self.assertEqual(data['interface availability'][0]['interfaceid'], 10)

    def test_history_data(self):
        pkt = ProxyDataPacket("testproxy")
        pkt.add_history_data(itemid=123, value="42", clock=1700000000, ns=500)
        data = json.loads(str(pkt))
        self.assertIn('history data', data)
        item = data['history data'][0]
        self.assertEqual(item['itemid'], '123')
        self.assertEqual(item['value'], '42')
        self.assertEqual(item['clock'], 1700000000)
        self.assertEqual(item['ns'], 500)
        self.assertEqual(item['id'], 1)
        self.assertEqual(item['state'], '0')

    def test_history_data_unsupported(self):
        pkt = ProxyDataPacket("testproxy")
        pkt.add_history_data(itemid=123, value="error msg", state=1, clock=1700000000)
        data = json.loads(str(pkt))
        self.assertEqual(data['history data'][0]['state'], '1')

    def test_autoregistration(self):
        pkt = ProxyDataPacket("testproxy")
        pkt.add_autoregistration(host="myhost", ip="10.0.0.1", host_metadata="meta1", clock=1700000000)
        data = json.loads(str(pkt))
        self.assertIn('auto registration', data)
        reg = data['auto registration'][0]
        self.assertEqual(reg['host'], 'myhost')
        self.assertEqual(reg['ip'], '10.0.0.1')
        self.assertEqual(reg['host_metadata'], 'meta1')

    def test_data_size(self):
        pkt = ProxyDataPacket("testproxy")
        self.assertEqual(pkt.data_size(), 0)
        pkt.add_history_data(itemid=1, value="v", clock=1700000000)
        pkt.add_history_data(itemid=2, value="v", clock=1700000000)
        pkt.add_interface_availability(interfaceid=1, available=1)
        self.assertEqual(pkt.data_size(), 3)

    def test_invalid_available_raises(self):
        pkt = ProxyDataPacket("testproxy")
        with self.assertRaises(TypeError):
            pkt.add_interface_availability(interfaceid=1, available=5)

    def test_no_host_availability_key(self):
        """Ensure old 'host availability' key is never used"""
        pkt = ProxyDataPacket("testproxy")
        pkt.add_interface_availability(interfaceid=1, available=1)
        data = json.loads(str(pkt))
        self.assertNotIn('host availability', data)


class TestProxy(unittest.TestCase):
    def test_session_generated(self):
        proxy = Proxy("testproxy", "127.0.0.1", 10051)
        self.assertEqual(len(proxy.session), 32)
        self.assertEqual(proxy.config_revision, 0)


class TestSenderDataPacket(unittest.TestCase):
    def test_packet_structure(self):
        pkt = SenderDataPacket()
        pkt.add("host1", "key1", "value1")
        data = json.loads(str(pkt))
        self.assertEqual(data['request'], 'sender data')
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['host'], 'host1')


if __name__ == '__main__':
    unittest.main()
