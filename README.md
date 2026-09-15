# glinet

[![CI](https://github.com/vithurshanselvarajah/python-glinet-router/actions/workflows/ci.yml/badge.svg)](https://github.com/vithurshanselvarajah/python-glinet-router/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/glinet)](https://pypi.org/project/glinet-router/)
[![License](https://img.shields.io/github/license/vithurshanselvarajah/python-glinet-router)](LICENSE)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

Async Python client for the GL.iNet router JSON-RPC API.

This library talks to the local JSON-RPC endpoint exposed by GL.iNet routers at
`/rpc`. It is the protocol layer used by the
[ha-glinet-router](https://github.com/vithurshanselvarajah/ha-glinet-router) Home
Assistant integration, but **it has no Home Assistant dependency** and is
designed to be used by anyone who needs to talk to a GL.iNet router from
Python.

## Features

- Async, `aiohttp`-based transport.
- Modular per-feature clients (`client.system`, `client.wifi`, `client.modem`,
  `client.wg_client`, `client.tailscale`, ...).
- Challenge/response authentication using `passlib` for the GL.iNet cipher
  algorithms (md5_crypt, sha256_crypt, sha512_crypt).
- Typed dataclasses for the common API responses.
- Dedicated handling for the firmware 4.9+ per-slot modem API.
- No Home Assistant dependency. Pure Python.

## Installation

```bash
pip install glinet
```

## Quick start

```python
import asyncio
from aiohttp import ClientSession
from glinet_router import GLinetApiClient, AuthenticationError


async def main() -> None:
    async with ClientSession() as session:
        client = GLinetApiClient(
            base_url="http://192.168.8.1/rpc",
            session=session,
            verify_ssl=False,
        )
        try:
            await client.authenticate("root", "your-admin-password")
        except AuthenticationError:
            print("Invalid credentials")
            return

        info = await client.system.get_info()
        print(f"Model: {info.model}  Firmware: {info.firmware_version}")

        status = await client.system.get_status()
        print(f"Uptime: {status.uptime}s  Load: {status.load_average}")

        clients = await client.clients.get_online()
        print(f"{len(clients)} clients online")


asyncio.run(main())
```

## Use cases

`glinet` is intended to be a **general-purpose** Python client for any project
that needs to talk to a GL.iNet router. It is not tied to Home Assistant.

- **Home Assistant** — see
  [ha-glinet-router](https://github.com/vithurshanselvarajah/ha-glinet-router)
  for the integration that depends on this package.
- **CLI scripts and cron jobs** — the package ships runnable examples under
  [`examples/`](examples/) and an installable `glinet` console script
  (`pip install 'glinet[cli]'`).
- **Async web services / microservices** — `glinet` is `aiohttp`-based and
  composes cleanly with any asyncio stack.
- **Custom dashboards / mobile companions** — see
  [`raw_rpc.py`](examples/raw_rpc.py) for an end-to-end example that does
  not require installing `passlib`.
- **Testing harnesses and CI** — the [`HttpTransport`](src/glinet/transport.py)
  abstraction makes it trivial to stub the network layer.

If you build something with `glinet` outside Home Assistant, please open a
PR adding your project to the wiki.

## Module map

The client is split into focused modules. Each attribute on `GLinetApiClient`
is one of the following `BaseModule` subclasses:

| Attribute | Coverage |
| --- | --- |
| `client.system` | Router info, status, reboot, KMWAN status |
| `client.modem` | Cellular modem info, status, SMS, traffic. Handles the 4.9+ per-slot API. |
| `client.wifi` | Wi-Fi interface config and per-interface enable/disable |
| `client.clients` | Connected client list, online filter, cache clear |
| `client.upgrade` | Firmware update checks, online status, online upgrade |
| `client.wg_client` | WireGuard client (unified 4.8 / 4.9 path) |
| `client.wg_server` | WireGuard server status, config, peer management |
| `client.ovpn_client` | OpenVPN client (unified 4.8 / 4.9 path) |
| `client.ovpn_server` | OpenVPN server status and config |
| `client.tailscale` | Tailscale config, state, connect/disconnect |
| `client.zerotier` | ZeroTier config and state |
| `client.repeater` | Repeater mode: status, scan, connect, saved APs |
| `client.fan` | Fan status, config, temperature threshold, test |
| `client.led` | System LED toggle |
| `client.macclone` | MAC clone query |
| `client.mcu` | MCU battery and OLED configuration |
| `client.firewall` | Firewall rules, port forwards, DMZ, WAN access, zones |
| `client.parental_control` | Parental control groups, schedules, filtering mode |
| `client.adguard` | AdGuard Home enable/disable |
| `client.black_white_list` | Black/whitelist client access lists |
| `client.diag` | Connectivity diagnostics |
| `client.kmwan` | KMWAN multi-WAN configuration |
| `client.mwan3` | MWAN3 multi-WAN configuration |

## Custom calls

For endpoints that are not yet wrapped by a module, `custom_call` builds and
dispatches a JSON-RPC call directly:

```python
await client.custom_call("module/method", {"param": "value"})
```

## Error model

All exceptions inherit from `APIClientError`:

- `APIClientError` — base
- `NonZeroResponse` — router returned a non-zero error code
- `AuthenticationError` — router rejected the credentials / session
- `TokenError` — session token expired or was rejected (code -1)
- `UnsuccessfulRequest` — transport / JSON decoding / HTTP failure

## Documentation

- [Home](docs/Home.md) — wiki landing page with a high-level overview and
  the full documentation index.
- [Authentication](docs/authentication.md) — challenge/response login flow,
  supported algorithms, and how to register a new one.
- [Errors](docs/errors.md) — exception hierarchy and the router error
  code → Python exception mapping.
- [Architecture](docs/architecture.md) — internal module map, request
  lifecycle, and design notes.
- [Router API notes](docs/router-api.md) — endpoint, payload structure,
  and full module inventory.
- [Modem API coverage](docs/modem-api.md) — firmware 4.8 vs 4.9
  differences and the helpers in `client.modem`.
- [VPN (WireGuard / OpenVPN)](docs/vpn.md) — the unified 4.8/4.9 client
  paths and the server-side helpers.
- [Tailscale](docs/tailscale.md) — connection state machine and the
  retry helpers.
- [Repeater](docs/repeater.md) — scan, connect, saved-APs, and bare mode.
- [Firewall](docs/firewall.md) — rules, ACLs, port forwards, DMZ, WAN
  access, and zones.
- [Parental control](docs/parental-control.md) — groups, time-window
  rules, and filtering mode.

## License

MIT — see [LICENSE](LICENSE).
