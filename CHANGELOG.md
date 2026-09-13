# Changelog

All notable changes to `glinet` are recorded here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-09-13

### Added
- Initial PyPI release of the GL.iNet router JSON-RPC client library.
- `GLinetApiClient` with module-based feature access (`client.system`,
  `client.wifi`, `client.modem`, `client.clients`, `client.upgrade`,
  `client.wg_client`, `client.wg_server`, `client.ovpn_client`,
  `client.ovpn_server`, `client.tailscale`, `client.zerotier`,
  `client.repeater`, `client.fan`, `client.led`, `client.macclone`,
  `client.mcu`, `client.firewall`, `client.parental_control`,
  `client.adguard`, `client.black_white_list`, `client.diag`, `client.kmwan`,
  `client.mwan3`).
- Async context manager support (`async with GLinetApiClient(...)`).
- Optional automatic `aiohttp.ClientSession` ownership.
- Pluggable authentication algorithm and digest tables
  (`GLinetApiClient.auth_hashers`, `GLinetApiClient.auth_digests`).
- Typed dataclasses for common responses (`RouterStatus`, `SystemInfo`,
  `WifiInterfaceInfo`, `ModemInfo`, `TailscaleConnection`).
- Error hierarchy: `APIClientError`, `NonZeroResponse`, `AuthenticationError`,
  `TokenError`, `UnsuccessfulRequest`. `aiohttp.ClientError` is re-exported as
  `glinet.ClientError` for convenience.
- Firmware-aware WireGuard and OpenVPN client modules that automatically pick
  the right endpoints for firmware 4.8 and 4.9+.
- Dedicated 4.9 per-slot modem handling in `client.modem`.
- Re-exported `custom_call` for ad-hoc JSON-RPC calls.
- Full test suite with mocked `aiohttp.ClientSession` (`pytest -q`).
- `py.typed` marker; library is PEP 561 compliant.
- Optional `[auth]` extra: install `glinet[auth]` to pull in `passlib` for
  `GLinetApiClient.authenticate()`. The library imports `passlib` lazily on
  first use, so consumers who only need read-only calls (or who supply
  their own `sid`) do not have to install it.
- Optional `[cli]` extra: install `glinet[cli]` to get the `glinet`
  console script (wraps `click`). Commands: `glinet info` and
  `glinet call <method>`. See `python -m glinet --help`.
- New `HttpTransport` protocol and `AiohttpTransport` default
  implementation in `glinet.transport`. Pass your own via the
  `transport=` kwarg on `GLinetApiClient` to swap the HTTP backend
  (`httpx`, mocks, custom connectors, etc.).
- Re-exports of `AiohttpTransport` and `HttpTransport` from the top-level
  `glinet` package.
- New runnable example scripts under `examples/`:
  - `examples/print_router_info.py` — authenticate and dump router info.
  - `examples/send_sms.py` — send an SMS via the router's SIM card.
  - `examples/raw_rpc.py` — make a raw JSON-RPC call without `passlib`.
- New docs: `Home.md` (wiki landing page), `authentication.md`,
  `errors.md`, `architecture.md`, `vpn.md`, `tailscale.md`,
  `repeater.md`, `firewall.md`, `parental-control.md`. The existing
  `router-api.md` and `modem-api.md` are now library-owned.
- `CONTRIBUTING.md` covering dev setup, conventional commits, the
  release process, and the "when to add a module" workflow.
- README badges for CI, PyPI, Python versions, license, and ruff.
- GitHub Actions CI workflow running `pytest` + `ruff` on Python 3.12
  and 3.13, plus a build job.
- Issue templates (bug report, feature request).

### Changed
- `custom_call("challenge", …)` and `custom_call("login", …)` raise
  `TypeError` if `params` is not a dict, instead of silently coercing to
  `{}`.
- `auth_hashers` is populated lazily inside `authenticate()` rather than
  at class definition time. Consumers who override the dict are no
  longer surprised by the defaults re-populating.

### Fixed
- `GLinetApiClient.authenticate()` raises an `ImportError` with
  install instructions when `passlib` is missing, instead of failing
  at module import time.
