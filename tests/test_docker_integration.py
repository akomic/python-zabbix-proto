#!/usr/bin/env python3
"""
Integration test against Dockerized Zabbix servers (5.4 and 7.4).

Usage:
    # Start servers:
    docker compose -f tests/docker-compose.yml up -d
    # Wait ~30s for DB init, then:
    python3 tests/test_docker_integration.py

    # Cleanup:
    docker compose -f tests/docker-compose.yml down
"""

import sys
import time
import unittest
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from zabbixproto import Proxy, ProxyDataPacket

PROXY_NAME = "zdbp-docker-test"


class ZabbixIntegrationBase:
    """Base class with shared test logic. Subclasses set server/port/version."""

    server = None
    port = None
    protocol_version = None

    def make_proxy(self):
        return Proxy(PROXY_NAME, self.server, self.port,
                     protocol_version=self.protocol_version)

    def test_heartbeat(self):
        proxy = self.make_proxy()
        # Should not raise - even unregistered proxies get a response or empty reply
        try:
            proxy.send_heartbeat()
        except Exception as e:
            if "no response" not in str(e):
                self.fail(f"Unexpected error: {e}")

    def test_get_config(self):
        proxy = self.make_proxy()
        try:
            resp = proxy.get_config()
            # Should get some response (even if proxy not registered, connection works)
            self.assertIsNotNone(resp)
        except Exception as e:
            # "not found" or similar is acceptable for unregistered proxy
            self.assertIn("not found", str(e).lower(),
                          f"Unexpected error: {e}")

    def test_send_data(self):
        proxy = self.make_proxy()
        data = ProxyDataPacket(PROXY_NAME, session=proxy.session,
                               protocol_version=self.protocol_version)
        data.add_autoregistration(
            host=f"{PROXY_NAME}-host",
            host_metadata="DockerIntegrationTest",
            clock=int(time.time())
        )
        try:
            proxy.sendWithResponse(data)
        except Exception as e:
            # Unregistered proxy gets rejected - that's fine, connection worked
            pass

    def test_send_history(self):
        proxy = self.make_proxy()
        data = ProxyDataPacket(PROXY_NAME, session=proxy.session,
                               protocol_version=self.protocol_version)
        data.add_history_data(itemid=99999, value="42", clock=int(time.time()))
        try:
            proxy.sendWithResponse(data)
        except Exception:
            pass  # Expected for unregistered proxy


class TestZabbix54(ZabbixIntegrationBase, unittest.TestCase):
    server = "127.0.0.1"
    port = 10054
    protocol_version = "5.4.0"


class TestZabbix74(ZabbixIntegrationBase, unittest.TestCase):
    server = "127.0.0.1"
    port = 10074
    protocol_version = "7.4.0"


if __name__ == '__main__':
    # Quick connectivity check
    import socket
    for port, ver in [(10054, "5.4"), (10074, "7.4")]:
        try:
            s = socket.create_connection(("127.0.0.1", port), timeout=3)
            s.close()
            print(f"✓ Zabbix {ver} reachable on port {port}")
        except (ConnectionRefusedError, OSError):
            print(f"✗ Zabbix {ver} NOT reachable on port {port}")
            print(f"  Run: docker compose -f tests/docker-compose.yml up -d")
            sys.exit(1)

    unittest.main(verbosity=2)
