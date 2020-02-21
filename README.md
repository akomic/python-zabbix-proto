Python Zabbix Proto
===================

Module supporting all Zabbix specific communication protocols.
At the moment Proxy protocol (active) is supported.

```python
from zabbixproto import ProxyAutoregistrationPacket, ProxyHistorydataPacket, Proxy
proxy = Proxy('testproxy', '127.0.0.1', 10051)

# Sending heartbeat to the Zabbix server
proxy.send_heartbeat()

# Getting "proxy configuration". Includes all hosts, items etc.
resp = proxy.get_config()
print(resp)

# Sending auto-registration packets
data = ProxyAutoregistrationPacket('testproxy-zdbp')
data.add('testhost', host_metadata="registerThisTestHost")
proxy.sendWithResponse(data)

# Sending metrics
data = ProxyHistorydataPacket('testproxy')
data.add(host='testhost', key='my.key',
         value=100)
# UNSUPPORTED
data.add(host='testhost', key='my.key2',
         value='Unsupported because of this and that', state=1)
proxy.sendWithResponse(data)
```
