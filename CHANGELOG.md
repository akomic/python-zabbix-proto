Python Zabbix Protocols
=======================

All notable changes to this project are documented here.
This project adheres to [Semantic Versioning](https://semver.org/).

## 2.2.1 (2026-08-04)
- Monotonic per-session `proxy data` value identifiers. Zabbix 7.x/6.x record the
  highest value `id` processed for a proxy session and silently DISCARD any value
  whose `id` is <= that high-water mark ("received value identifier X is lower
  than the last processed value identifier Y"). Previously `id` restarted at 1 for
  every packet, so a proxy that reuses one session across many packets had all but
  the first packet dropped by the server. `id` is now drawn from a single
  process-wide, thread-safe counter so every session emits strictly increasing
  ids across packets and sender threads. (Zabbix 5.0 did not enforce this, so the
  bug was invisible on 5.x and only surfaced on 7.x.)
- `Proxy(...)` now accepts an optional `session` token so a multi-threaded client
  (separate reader/sender `Proxy` instances) can share one token and mirror a
  native proxy's single-session model. When omitted, a token is generated as
  before (v5.x/6.x remain session-less).

## 2.2.1rc1 (2026-07-30)
- `Proxy(...)` now accepts an optional `session` token. A Zabbix 7.x proxy uses a
  single session token for its whole lifetime; injecting one lets a multi-threaded
  client (separate reader/sender `Proxy` instances) share one token and mirror a
  native proxy instead of presenting many sessions. When omitted, a token is
  generated as before (v5.x/6.x remain session-less).
- Monotonic per-session `proxy data` value identifiers. Zabbix 7.x/6.x record the
  highest value `id` processed for a proxy session and silently DISCARD any value
  whose `id` is <= that high-water mark ("received value identifier X is lower
  than the last processed value identifier Y"). Previously `id` restarted at 1 for
  every packet, so a proxy that reuses one session across many packets had all but
  the first packet dropped by the server. `id` is now drawn from a single
  process-wide, thread-safe counter so every session emits strictly increasing
  ids across packets and sender threads. (Zabbix 5.0 did not enforce this, so the
  bug was invisible on 5.x and only surfaced on 7.x.)

## 2.2.0 (2026-07-28)
- Version-aware `Proxy.send_heartbeat()`: Zabbix 7.x sends an empty `proxy data`
  keepalive (the `proxy heartbeat` request was removed in 7.0), while 5.x/6.x
  continue to send `proxy heartbeat`. Fixes proxy liveness reporting on 7.x.
- Versioning is now derived from Git tags via `setuptools-scm` (tag `vX.Y.Z`
  builds version `X.Y.Z`; pre-release tags such as `v2.2.0rc1` build `2.2.0rc1`).
  CI checkouts use `fetch-depth: 0` so tags are available to the build.

## 2.1.1 (2026-07-28)
- Packaging migrated from `distutils`/`setup.py` to `pyproject.toml` (PEP 621).
  Fixes the build on Python 3.12+ where `distutils` was removed. Corrects the
  stale `download_url` (was pointing at v2.0.0).
- Removed the spurious `datetime` install dependency (it is part of the stdlib;
  the PyPI `datetime` package is an unrelated project).
- Malformed protocol version strings now emit a warning instead of silently
  defaulting to the newest protocol.
- Transport hardening in `client.py`: per-connection socket timeout (removed the
  process-global `setdefaulttimeout` and the fixed `time.sleep`), guaranteed
  socket cleanup via `try/finally`, and narrowed exception handling.
- CI test matrix extended to Python 3.13 and 3.14.

## 2.1.0 (2026-05-11)
- Full Zabbix 7.x protocol support alongside 5.x/6.x backward compatibility.
- Proxy sessions (`session`) and incremental config sync (`config_revision`) for v7.
- v7 `interface availability` vs. v5 `host availability` handled transparently
  via `add_host_availability()` / `add_interface_availability()`.
- Nanosecond (`ns`) field added to history data on v7.
- Protocol version normalization to `major.0.0`.

## 2.0.1 (2026-04-14)
- Fix heartbeat error handling for Zabbix 7.0.

## 2.0.0 (2026-04-14)
- Initial Zabbix 7.0 support.
- Added ZBXD compression support.
- Added integration tests; pinned CI actions to commit SHAs.

## 1.0.1 (2021-03-07)
- Autoregistration bugfix.

## 1.0.0 (2020-10-17)
- Zabbix 5.0 support.

## 0.0.9 (2020-05-11)
- Sender protocol support.

## 0.0.1 (2020-02-21)
- Initial release.
