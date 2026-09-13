# glinet

`glinet` is a standalone async Python client for the GL.iNet router
JSON-RPC API. It is the protocol layer used by the
[ha-glinet-router](https://github.com/vithurshanselvarajah/ha-glinet-router)
Home Assistant integration, but it is also usable on its own from any
asyncio application.

- **Package name:** `glinet`
- **PyPI:** https://pypi.org/project/glinet/
- **Source:** https://github.com/vithurshanselvarajah/python-glinet-router
- **Python:** 3.12+
- **Transport:** `aiohttp`
- **Authentication:** challenge/response using `passlib` (md5_crypt, sha256_crypt, sha512_crypt)

## What you get

- One `GLinetApiClient` class with a per-feature module attribute
  (`client.system`, `client.wifi`, `client.modem`, `client.wg_client`,
  `client.tailscale`, …).
- Typed dataclasses for common responses (`RouterStatus`, `SystemInfo`,
  `WifiInterfaceInfo`, `ModemInfo`, `TailscaleConnection`).
- Async context manager (`async with GLinetApiClient(...)`).
- A pluggable hasher / digest table so new router firmware variants can be
  supported without subclassing.
- Dedicated handling for the firmware 4.9+ per-slot modem API.
- A `custom_call` escape hatch for endpoints that don't have a wrapper yet.

## Install

```bash
pip install glinet
```

## Quick start

```python
import asyncio
from glinet import GLinetApiClient


async def main() -> None:
    async with GLinetApiClient("http://192.168.8.1/rpc") as client:
        await client.authenticate("root", "your-admin-password")
        info = await client.system.get_info()
        print(f"Model: {info.model}  Firmware: {info.firmware_version}")


asyncio.run(main())
```

See [Quick start →](README.md#quick-start) for the full example.

## Documentation index

| Page | Purpose |
| --- | --- |
| [Authentication](authentication.md) | How the challenge/response login works, supported hashers, and how to add a new one. |
| [Errors](errors.md) | Exception hierarchy and the GL.iNet error code → Python exception mapping. |
| [Architecture](architecture.md) | Internal module map, request lifecycle, and design notes. |
| [Router API notes](router-api.md) | Endpoint, payload structure, and the full module inventory. |
| [Modem API coverage](modem-api.md) | Firmware 4.8 vs 4.9 differences and the helpers in `client.modem`. |
| [VPN (WireGuard / OpenVPN)](vpn.md) | The unified 4.8/4.9 client paths and the helper methods. |
| [Tailscale](tailscale.md) | Connection states, `connect`/`disconnect` retry loops, and config helpers. |
| [Repeater](repeater.md) | Scan, connect, saved-AP list, and bare-mode entry/exit. |
| [Firewall](firewall.md) | Rules, port forwards, ACLs, DMZ, WAN access, and zones. |
| [Parental control](parental-control.md) | Groups, schedules, filtering mode, and access lists. |
| [Contributing](../CONTRIBUTING.md) | Dev setup, testing, and release process. |
| [CI & releases](ci-release.md) | Trusted publishing to PyPI and how releases get cut. |

## Where this library fits

```
┌─────────────────────────────────────┐
│  ha-glinet-router (HA integration)  │   ← entities, services, coordinator
└──────────────────┬──────────────────┘
                   │ depends on
                   ▼
┌─────────────────────────────────────┐
│  glinet (this package)              │   ← JSON-RPC, auth, modules
└──────────────────┬──────────────────┘
                   │ uses
                   ▼
┌─────────────────────────────────────┐
│  GL.iNet router /rpc endpoint       │
└─────────────────────────────────────┘
```

If you are writing a non-Home Assistant application, you only need
`glinet` — nothing in this package depends on Home Assistant.

## License

MIT — see [LICENSE](../LICENSE).
