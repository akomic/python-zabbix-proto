DEFAULT_PROTOCOL_VERSION = "7.0.0"


class ResponseException(Exception):
    pass


def is_v7(version):
    """Return True if version string indicates Zabbix 7.x+ protocol."""
    try:
        major = int(version.split('.')[0])
        return major >= 7
    except (ValueError, IndexError):
        return True
