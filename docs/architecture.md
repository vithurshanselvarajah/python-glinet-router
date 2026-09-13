# Architecture

This page documents the internal layout of the `glinet` package, the
request lifecycle, and the design choices that matter if you want to
extend the library.

## Package layout

```
src/glinet/
├── __init__.py          Re-exports the public API (ClientError, models,
│                        exceptions, GLinetApiClient).
├── client.py            GLinetApiClient + JSON-RPC payload helpers +
│                        authentication + custom_call.
├── const.py             Timeouts and firmware version tuples.
├── exceptions.py        APIClientError hierarchy.
├── models.py            Typed dataclasses (RouterStatus, SystemInfo, …).
├── utils.py             decode_firmware_version helper.
└── modules/
    ├── __init__.py      Re-exports all module classes.
    ├── base.py          BaseModule — wraps _call around _send_request.
    ├── adguard.py       AdGuardModule
    ├── black_white_list.py  BlackWhiteListModule
    ├── clients.py       ClientsModule
    ├── diag.py          DiagModule
    ├── fan.py           FanModule
    ├── firewall.py      FirewallModule
    ├── kmwan.py         KmwanModule
    ├── led.py           LedModule
    ├── macclone.py      MacCloneModule
    ├── mcu.py           McuModule
    ├── modem.py         ModemModule — firmware 4.8/4.9 aware.
    ├── mwan3.py         Mwan3Module
    ├── ovpn_client.py   OvpnClientModule + legacy OvpnModule + VpnClientModule.
    ├── ovpn_server.py   OvpnServerModule
    ├── parental_control.py  ParentalControlModule
    ├── repeater.py      RepeaterModule
    ├── system.py        SystemModule
    ├── tailscale.py     TailscaleModule
    ├── upgrade.py       UpgradeModule
    ├── vpn_client.py    VpnClientModule
    ├── wg_client.py     WgClientModule + WireGuardModule.
    ├── wg_server.py     WgServerModule
    ├── wifi.py          WifiModule
    └── zerotier.py      ZeroTierModule
```

Each module is a `BaseModule` subclass that receives the
`GLinetApiClient` instance in `__init__` and accesses its private helpers
(`_send_request`, `_build_sid_payload`, `sid`, `_firmware_version`,
`_is_firmware_at_least`).

## Request lifecycle

```text
client.<module>.<method>(...)
        │
        ▼
BaseModule._call(module, method, params)
        │  builds payload via _build_sid_payload("call",
        │  [module, method, params], self._client.sid)
        ▼
GLinetApiClient._send_request(payload)
        │  POST to <base_url> with timeout + ssl setting
        ▼
_extract_response_data(response)
        │  parses JSON-RPC payload, raises:
        │  - UnsuccessfulRequest on HTTP / JSON errors
        │  - TokenError / AuthenticationError / NonZeroResponse on error codes
        │  - APIClientError on unexpected shapes
        ▼
Python value (dict / list / scalar)
```

The `call` payload always has the form:

```json
{
  "method": "call",
  "jsonrpc": "2.0",
  "params": ["<sid>", "<module>", "<method>", { /* params */ }],
  "id": 0
}
```

The router wraps the call result in a `result` envelope; the library
unwraps it before returning to the caller.

## Firmware version detection

`GLinetApiClient` lazily fetches `system.get_info` the first time
`_is_firmware_at_least` is called and caches the parsed firmware tuple
in `_firmware_version`. Modules that depend on firmware differences
(check `client.modem`, `client.wg_client`, `client.ovpn_client`) use
this to pick between the legacy 4.8 endpoint shape and the 4.9+
per-slot endpoints.

If you call a method that needs the firmware version *before* you've
authenticated, the call will fail with `APIClientError`. Authenticate
first.

## Per-module design

### `BaseModule`

Holds a back-reference to the client so subclasses can:

- call `self._client._send_request(payload, ...)` directly when they need
  a custom timeout (see `repeater.scan`, which uses `SCAN_TIMEOUT`).
- inspect `self._client.sid` and `self._client._firmware_version`.
- check `self._client._is_firmware_at_least(...)`.

`BaseModule` deliberately does not expose a public `client` property —
the convention is `_call(module, method, params, timeout_seconds=…)`.

### `GLinetApiClient`

Owns:

- `_base_url` — the `/rpc` endpoint, with no trailing slash.
- `_ssl_setting` — `None` for verify, `False` for skip.
- `_session` — `aiohttp.ClientSession`, either user-supplied or owned.
- `_owns_session` — `True` when the client created the session itself;
  controls whether `close()` actually closes it.
- `sid` — current session id (or `None` if not authenticated).
- `_firmware_version` — cached firmware tuple.

Provides:

- `authenticate(username, password)` — challenge/response login.
- `is_router_reachable(username)` — reachability probe (no password).
- `custom_call(method, params)` — escape hatch for endpoints not yet
  wrapped by a module.
- `__aenter__` / `__aexit__` / `close()` — async context manager.

### `auth_hashers` / `auth_digests`

Class-level dicts that map GL.iNet `alg` values to `passlib` hashers and
GL.iNet `hash-method` values to `hashlib` constructors. Override at
instance level (or via subclass) to support new firmware variants.
See [Authentication](authentication.md) for examples.

## Extending the library

### Adding a new module endpoint

1. Edit the relevant `src/glinet/modules/<name>.py` (or create a new one).
2. Add a method on the existing class — or create a new `BaseModule`
   subclass if the endpoint belongs to a new feature.
3. Attach the new module to `GLinetApiClient.__init__` in
   `src/glinet/client.py`.
4. Re-export the class from `src/glinet/modules/__init__.py`.
5. Add tests in `tests/test_<name>.py` using the `FakeSession` /
   `FakeResponse` doubles from `tests/_fakes.py`.
6. Add a docs page under `docs/` if the new surface is non-trivial.

### Adding a new firmware algorithm

Just extend `auth_hashers` or `auth_digests` at runtime — no library
changes needed. See [Authentication](authentication.md).

## See also

- [Router API notes](router-api.md) — the wire-level protocol.
- [Modem API coverage](modem-api.md) — concrete example of firmware-aware
  module design.
