import json
import unittest
from zabbixproto import DEFAULT_PROTOCOL_VERSION, PROXY_VERSION, is_v7
from zabbixproto.proxypackets import (
    Proxy, ProxyHeartbeatPacket, ProxyConfigPacket, ProxyDataPacket
)
from zabbixproto.senderpackets import SenderDataPacket


class TestConfig(unittest.TestCase):
    def test_default_version(self):
        self.assertEqual(DEFAULT_PROTOCOL_VERSION, "7.0.0")

    def test_backward_compat_alias(self):
        self.assertEqual(PROXY_VERSION, DEFAULT_PROTOCOL_VERSION)

    def test_is_v7(self):
        self.assertTrue(is_v7("7.0.0"))
        self.assertTrue(is_v7("7.4.0"))
        self.assertTrue(is_v7("8.0.0"))
        self.assertFalse(is_v7("5.0.0"))
        self.assertFalse(is_v7("5.4.0"))
        self.assertFalse(is_v7("6.0.0"))


class TestProxyV7(unittest.TestCase):
    def test_session_generated(self):
        proxy = Proxy("testproxy", "127.0.0.1", 10051)
        self.assertEqual(len(proxy.session), 32)
        self.assertEqual(proxy.config_revision, 0)
        self.assertEqual(proxy.protocol_version, "7.0.0")

    def test_explicit_version(self):
        proxy = Proxy("testproxy", "127.0.0.1", 10051, protocol_version="7.4.0")
        self.assertEqual(proxy.protocol_version, "7.0.0")  # normalized
        self.assertIsNotNone(proxy.session)


class TestProxyV5(unittest.TestCase):
    def test_no_session(self):
        proxy = Proxy("testproxy", "127.0.0.1", 10051, protocol_version="5.4.0")
        self.assertIsNone(proxy.session)
        self.assertEqual(proxy.protocol_version, "5.0.0")  # normalized


class TestHeartbeatV7(unittest.TestCase):
    def test_packet_structure(self):
        pkt = ProxyHeartbeatPacket("testproxy", "7.0.0")
        data = json.loads(str(pkt))
        self.assertEqual(data['request'], 'proxy heartbeat')
        self.assertEqual(data['host'], 'testproxy')
        self.assertEqual(data['version'], '7.0.0')


class TestHeartbeatV5(unittest.TestCase):
    def test_packet_structure(self):
        pkt = ProxyHeartbeatPacket("testproxy", "5.4.0")
        data = json.loads(str(pkt))
        self.assertEqual(data['version'], '5.0.0')  # normalized


class TestConfigPacketV7(unittest.TestCase):
    def test_includes_session_and_revision(self):
        pkt = ProxyConfigPacket("testproxy", "7.0.0", "abc123", 5)
        data = json.loads(str(pkt))
        self.assertEqual(data['session'], 'abc123')
        self.assertEqual(data['config_revision'], 5)
        self.assertEqual(data['version'], '7.0.0')


class TestConfigPacketV5(unittest.TestCase):
    def test_no_session_or_revision(self):
        pkt = ProxyConfigPacket("testproxy", "5.4.0", None, 0)
        data = json.loads(str(pkt))
        self.assertNotIn('session', data)
        self.assertNotIn('config_revision', data)
        self.assertEqual(data['version'], '5.0.0')  # normalized


class TestDataPacketV7(unittest.TestCase):
    def test_has_session(self):
        pkt = ProxyDataPacket("testproxy", session="sess123", protocol_version="7.0.0")
        data = json.loads(str(pkt))
        self.assertEqual(data['session'], 'sess123')
        self.assertEqual(data['version'], '7.0.0')

    def test_interface_availability(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="7.0.0")
        pkt.add_interface_availability(interfaceid=42, available=1)
        data = json.loads(str(pkt))
        self.assertIn('interface availability', data)
        self.assertNotIn('host availability', data)
        self.assertEqual(data['interface availability'][0]['interfaceid'], 42)

    def test_host_availability_alias_uses_interfaceid(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="7.0.0")
        pkt.add_host_availability(hostid=10, interfaceid=42, available=2, error='down')
        data = json.loads(str(pkt))
        self.assertIn('interface availability', data)
        self.assertEqual(data['interface availability'][0]['interfaceid'], 42)

    def test_history_data_has_ns(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="7.0.0")
        pkt.add_history_data(itemid=123, value="42", clock=1700000000, ns=500)
        data = json.loads(str(pkt))
        self.assertEqual(data['history data'][0]['ns'], 500)

    def test_history_data_id_counter(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="7.0.0")
        pkt.add_history_data(itemid=1, value="a", clock=1700000000)
        pkt.add_history_data(itemid=2, value="b", clock=1700000000)
        data = json.loads(str(pkt))
        self.assertEqual(data['history data'][0]['id'], 1)
        self.assertEqual(data['history data'][1]['id'], 2)


class TestDataPacketV5(unittest.TestCase):
    def test_no_session(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        data = json.loads(str(pkt))
        self.assertNotIn('session', data)
        self.assertEqual(data['version'], '5.0.0')  # normalized

    def test_host_availability_uses_hostid(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        pkt.add_host_availability(hostid=10, interfaceid=42, available=1)
        data = json.loads(str(pkt))
        self.assertIn('host availability', data)
        self.assertNotIn('interface availability', data)
        self.assertEqual(data['host availability'][0]['hostid'], 10)

    def test_host_availability_with_snmp(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        pkt.add_host_availability(hostid=10, available=2, error='down',
                                  snmp_available=2, snmp_error='timeout')
        data = json.loads(str(pkt))
        metric = data['host availability'][0]
        self.assertEqual(metric['hostid'], 10)
        self.assertEqual(metric['snmp_available'], 2)
        self.assertEqual(metric['snmp_error'], 'timeout')

    def test_interface_availability_emits_host_availability(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        pkt.add_interface_availability(interfaceid=10, available=1)
        data = json.loads(str(pkt))
        self.assertIn('host availability', data)
        self.assertEqual(data['host availability'][0]['hostid'], 10)

    def test_history_data_no_ns(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        pkt.add_history_data(itemid=123, value="42", clock=1700000000)
        data = json.loads(str(pkt))
        self.assertNotIn('ns', data['history data'][0])

    def test_history_data_unsupported(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        pkt.add_history_data(itemid=123, value="error", state=1, clock=1700000000)
        data = json.loads(str(pkt))
        self.assertEqual(data['history data'][0]['state'], '1')


class TestDataPacketCommon(unittest.TestCase):
    def test_autoregistration(self):
        for ver in ["5.4.0", "7.0.0"]:
            pkt = ProxyDataPacket("testproxy", protocol_version=ver)
            pkt.add_autoregistration(host="myhost", ip="10.0.0.1",
                                     host_metadata="meta1", clock=1700000000)
            data = json.loads(str(pkt))
            self.assertIn('auto registration', data)
            reg = data['auto registration'][0]
            self.assertEqual(reg['host'], 'myhost')
            self.assertEqual(reg['ip'], '10.0.0.1')
            self.assertEqual(reg['host_metadata'], 'meta1')

    def test_data_size(self):
        for ver in ["5.4.0", "7.0.0"]:
            pkt = ProxyDataPacket("testproxy", protocol_version=ver)
            self.assertEqual(pkt.data_size(), 0)
            pkt.add_history_data(itemid=1, value="v", clock=1700000000)
            pkt.add_history_data(itemid=2, value="v", clock=1700000000)
            pkt.add_host_availability(hostid=1, interfaceid=1, available=1)
            self.assertEqual(pkt.data_size(), 3)

    def test_invalid_available_raises(self):
        for ver in ["5.4.0", "7.0.0"]:
            pkt = ProxyDataPacket("testproxy", protocol_version=ver)
            with self.assertRaises(TypeError):
                pkt.add_interface_availability(interfaceid=1, available=5)


class TestDataPacketV5Validation(unittest.TestCase):
    def test_invalid_snmp_available_raises(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        with self.assertRaises(TypeError):
            pkt.add_host_availability(hostid=1, available=1, snmp_available=5)

    def test_invalid_ipmi_available_raises(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        with self.assertRaises(TypeError):
            pkt.add_host_availability(hostid=1, available=1, ipmi_available=-1)

    def test_invalid_jmx_available_raises(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        with self.assertRaises(TypeError):
            pkt.add_host_availability(hostid=1, available=1, jmx_available="bad")

    def test_host_availability_with_ipmi(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        pkt.add_host_availability(hostid=10, available=1, ipmi_available=2, ipmi_error='no response')
        data = json.loads(str(pkt))
        metric = data['host availability'][0]
        self.assertEqual(metric['ipmi_available'], 2)
        self.assertEqual(metric['ipmi_error'], 'no response')

    def test_host_availability_with_jmx(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        pkt.add_host_availability(hostid=10, available=1, jmx_available=2, jmx_error='conn refused')
        data = json.loads(str(pkt))
        metric = data['host availability'][0]
        self.assertEqual(metric['jmx_available'], 2)
        self.assertEqual(metric['jmx_error'], 'conn refused')

    def test_host_availability_no_hostid_raises(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        with self.assertRaises(TypeError):
            pkt.add_host_availability(hostid=None, available=1)


class TestDataPacketV7Validation(unittest.TestCase):
    def test_interface_availability_no_id_raises(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="7.0.0")
        with self.assertRaises(TypeError):
            pkt.add_interface_availability(interfaceid=None, available=1)

    def test_auto_generates_session(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="7.0.0")
        data = json.loads(str(pkt))
        self.assertEqual(len(data['session']), 32)


class TestDataPacketErrorCases(unittest.TestCase):
    def test_history_data_invalid_clock_raises(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="7.0.0")
        with self.assertRaises(TypeError):
            pkt.add_history_data(itemid=1, value="v", clock="not a number")

    def test_history_data_invalid_state_raises(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="7.0.0")
        with self.assertRaises(TypeError):
            pkt.add_history_data(itemid=1, value="v", clock=1700000000, state=2)

    def test_autoregistration_invalid_clock_raises(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="7.0.0")
        with self.assertRaises(TypeError):
            pkt.add_autoregistration(host="h", clock="bad")


class TestVersionNormalization(unittest.TestCase):
    def test_garbage_input(self):
        from zabbixproto.proxypackets import _normalize_version
        self.assertEqual(_normalize_version("abc"), "7.0.0")
        self.assertEqual(_normalize_version(""), "7.0.0")

    def test_valid_versions(self):
        from zabbixproto.proxypackets import _normalize_version
        self.assertEqual(_normalize_version("5.4.3"), "5.0.0")
        self.assertEqual(_normalize_version("7.4.0"), "7.0.0")
        self.assertEqual(_normalize_version("6.0.0"), "6.0.0")


class TestConfigPacketV7NoSession(unittest.TestCase):
    def test_no_session_omits_fields(self):
        pkt = ProxyConfigPacket("testproxy", "7.0.0", None, 0)
        data = json.loads(str(pkt))
        self.assertNotIn('session', data)
        self.assertNotIn('config_revision', data)


class TestPacketVersionField(unittest.TestCase):
    def test_v5_packets_use_v5_version(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="5.4.0")
        data = json.loads(str(pkt))
        self.assertEqual(data['version'], '5.0.0')

    def test_v7_packets_use_v7_version(self):
        pkt = ProxyDataPacket("testproxy", protocol_version="7.0.0")
        data = json.loads(str(pkt))
        self.assertEqual(data['version'], '7.0.0')


class TestSenderDataPacket(unittest.TestCase):
    def test_packet_structure(self):
        pkt = SenderDataPacket()
        pkt.add("host1", "key1", "value1")
        data = json.loads(str(pkt))
        self.assertEqual(data['request'], 'sender data')
        self.assertEqual(len(data['data']), 1)

    def test_clock_is_int(self):
        pkt = SenderDataPacket()
        data = json.loads(str(pkt))
        self.assertIsInstance(data['clock'], int)

    def test_multiple_items(self):
        pkt = SenderDataPacket()
        pkt.add("host1", "key1", "val1")
        pkt.add("host2", "key2", "val2")
        data = json.loads(str(pkt))
        self.assertEqual(len(data['data']), 2)
        self.assertEqual(data['data'][0]['host'], 'host1')
        self.assertEqual(data['data'][1]['host'], 'host2')


if __name__ == '__main__':
    unittest.main()
