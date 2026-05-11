from .config import DEFAULT_PROTOCOL_VERSION, ResponseException, is_v7
from .client import Client
from .proxypackets import Proxy, ProxyHeartbeatPacket, ProxyConfigPacket, ProxyDataPacket
from .senderpackets import Sender, SenderDataPacket

# Backward compat alias
PROXY_VERSION = DEFAULT_PROTOCOL_VERSION
