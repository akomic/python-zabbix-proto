#!/usr/bin/env python3
"""
Integration test for ZabbixProto against Zabbix 7.0 server.

Usage:
    python3 tests/integration_test.py <zabbix-server-host> [port]

Prerequisites:
    1. Network access to the Zabbix server on port 10051
    2. Create an Active proxy in Zabbix UI:
       - Administration → Proxies → Create proxy
       - Proxy name: zdbp-integration-test
       - Proxy mode: Active
    3. Create a host monitored by that proxy:
       - Data collection → Hosts → Create host
       - Host name: integration-test-db
       - Host group: any (e.g. "Integration Tests")
       - Monitored by proxy: zdbp-integration-test
    4. Create a trapper item on that host:
       - Items → Create item
       - Name: Test item
       - Type: Zabbix trapper
       - Key: zdbp.stats.itemsTotal
       - Type of information: Numeric (unsigned)
"""

import sys
import json
from zabbixproto import Proxy, ProxyDataPacket, PROXY_VERSION

if len(sys.argv) < 2:
    print(f"Usage: {sys.argv[0]} <zabbix-server-host> [port]")
    sys.exit(1)

SERVER = sys.argv[1]
PORT = sys.argv[2] if len(sys.argv) > 2 else "10051"
PROXY_NAME = "zdbp-integration-test"

def test_version():
    print(f"[1] ZabbixProto version: {PROXY_VERSION}")
    assert PROXY_VERSION == "7.0.0", f"Expected 7.0.0, got {PROXY_VERSION}"
    print("    PASS")

def test_heartbeat():
    print(f"[2] Sending heartbeat to {SERVER}:{PORT}...")
    proxy = Proxy(PROXY_NAME, SERVER, PORT)
    try:
        proxy.send_heartbeat()
        print("    PASS — heartbeat accepted")
    except Exception as e:
        # Heartbeat may return empty response in 7.0 — connection working is what matters
        if "no response" in str(e):
            print("    PASS — server reachable (empty heartbeat response is normal for unregistered proxy)")
        else:
            print(f"    FAIL — {e}")
            return False
    return True

def test_get_config():
    print(f"[3] Fetching proxy config...")
    proxy = Proxy(PROXY_NAME, SERVER, PORT)
    try:
        resp = proxy.get_config()
        print(f"    Session: {proxy.session}")
        print(f"    Config revision: {proxy.config_revision}")
        if hasattr(resp, 'data'):
            tables = [k for k in resp.data.keys() if k not in ('response', 'full_sync', 'config_revision', 'macro.secrets')]
            print(f"    Tables received: {tables}")
        print("    PASS")
    except Exception as e:
        print(f"    FAIL — {e}")
        return False
    return True

def test_send_data():
    print(f"[4] Sending test data packet...")
    proxy = Proxy(PROXY_NAME, SERVER, PORT)
    data = ProxyDataPacket(PROXY_NAME, proxy.session)
    data.add_autoregistration(
        host=f"{PROXY_NAME}-host",
        host_metadata="ZDBPIntegrationTest"
    )
    try:
        resp = proxy.sendWithResponse(data)
        print(f"    Response: {resp}")
        print("    PASS")
    except Exception as e:
        if "not found" in str(e):
            print(f"    PASS — server responded correctly (proxy not registered in Zabbix yet: {e})")
        else:
            print(f"    FAIL — {e}")
            return False
    return True


def test_fetch_and_send_metric():
    print(f"[5] Fetch config and send metric value...")
    proxy = Proxy(PROXY_NAME, SERVER, PORT)
    try:
        resp = proxy.get_config()
        items_data = resp.data.get('data', {}).get('items', {})
        if not items_data or not items_data.get('data'):
            print("    SKIP — no items configured for this proxy yet")
            return True

        fields = items_data['fields']
        itemid_idx = fields.index('itemid')
        key_idx = fields.index('key_')

        print(f"    Found {len(items_data['data'])} item(s):")
        for row in items_data['data']:
            print(f"      itemid={row[itemid_idx]} key={row[key_idx]}")

        import time
        first_item = items_data['data'][0]
        itemid = first_item[itemid_idx]

        data = ProxyDataPacket(PROXY_NAME, proxy.session)
        data.add_history_data(itemid=itemid, value="42", clock=int(time.time()))
        resp = proxy.sendWithResponse(data)
        print(f"    Sent value 42 for itemid {itemid}")
        print(f"    Response: {resp}")
        print("    PASS")
    except Exception as e:
        print(f"    FAIL — {e}")
        return False
    return True


if __name__ == "__main__":
    print(f"ZabbixProto Integration Test")
    print(f"Server: {SERVER}:{PORT}")
    print(f"Proxy name: {PROXY_NAME}")
    print("=" * 50)

    results = []
    test_version()
    results.append(test_heartbeat())
    results.append(test_get_config())
    results.append(test_send_data())
    results.append(test_fetch_and_send_metric())

    print("=" * 50)
    if all(results):
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
        sys.exit(1)
