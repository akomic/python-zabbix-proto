import warnings

DEFAULT_PROTOCOL_VERSION = "7.0.0"


class ResponseException(Exception):
    pass


def is_v7(version):
    """Return True if the version string indicates Zabbix 7.x+ protocol.

    On malformed input we cannot know the intended protocol, so we fall back to
    the default (newest) protocol rather than guessing silently. A warning is
    emitted so the miscommunication is visible instead of hidden.
    """
    try:
        major = int(str(version).split('.')[0])
        return major >= 7
    except (ValueError, IndexError, AttributeError):
        warnings.warn(
            "Unparseable protocol version {!r}; falling back to default {}".format(
                version, DEFAULT_PROTOCOL_VERSION),
            stacklevel=2,
        )
        return int(DEFAULT_PROTOCOL_VERSION.split('.')[0]) >= 7
