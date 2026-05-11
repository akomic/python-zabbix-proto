Python Zabbix Proto
===================

Module supporting all Zabbix specific communication protocols.
At the moment Proxy (active) and sender protocols are supported.

# Zabbix server supported versions
| Zabbix Proto            | Zabbix   |
| ----------------------- | -------- |
| <=0.0.9                 | <=3.2    |
| >=1.0.0, <2.0.0        | 5.0-6.x |
| >=2.1.0                 | 5.0-7.x |


# Installation

```bash
pip install zabbixproto
```

# Proxy

By default the library uses Zabbix 7.x protocol. To communicate with older servers, pass `protocol_version`:

```python
from datetime import datetime
from zabbixproto import Proxy, ProxyDataPacket

## Zabbix 7.x (default)
proxy = Proxy('testproxy', '127.0.0.1', 10051)

## Zabbix 5.x/6.x
proxy = Proxy('testproxy', '127.0.0.1', 10051, protocol_version="5.4.0")

## Sending heartbeat to the Zabbix server
proxy.send_heartbeat()

## Getting "proxy configuration". Includes all hosts, items etc.
resp = proxy.get_config()
print(resp)

data = ProxyDataPacket('testproxy', session=proxy.session,
                       protocol_version=proxy.protocol_version)

## Sending auto-registration packets
data.add_autoregistration(
    host="testhost",
    host_metadata="registerThisTestHost"
)

## Sending metrics
data.add_history_data(
    itemid=12345,
    value=100,
    clock=int(datetime.now().timestamp())
)

## UNSUPPORTED
data.add_history_data(
    itemid=12345,
    value="Unsupported because of this and that",
    state=1,
    clock=int(datetime.now().timestamp())
)

## Unavailable host (v7: interface availability, v5: host availability)
data.add_host_availability(
    hostid=100,
    available=2, # 0 - Unknown, 1 - Available, 2 - Unavailable
    error='Web site is down!'
)

print(proxy.sendWithResponse(data))
```

# Sender
```python
from zabbixproto import Sender, SenderDataPacket

sender = Sender('127.0.0.1', 10051)
packet = SenderDataPacket()
packet.add("hostname", "key", "value")
sender.sendWithResponse(packet)
```
