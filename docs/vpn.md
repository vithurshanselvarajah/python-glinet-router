# VPN (WireGuard / OpenVPN)

The library exposes two unified client modules — `client.wg_client` and
`client.ovpn_client` — that automatically pick the correct endpoint
shape based on the router firmware version. The server side is split
into `client.wg_server` and `client.ovpn_server` and is firmware-agnostic.

## Firmware-aware client paths

| Module | Firmware 4.8 and earlier | Firmware 4.9 and later |
| --- | --- | --- |
| `client.wg_client.get_wireguard_state()` | `wg-client/get_status` | `vpn-client/get_status` |
| `client.wg_client.start_wireguard_client(group_id, peer_id)` | `vpn-client/set_tunnel(peer_id, True)` | `vpn-client/set_tunnel(type="wireguard", group_id, peer_id, …)` |
| `client.ovpn_client.get_status()` | `ovpn-client` aggregate endpoints | `vpn-client/get_status` |

The router advertises the firmware version from `system/get_info`; the
client caches it the first time a firmware-aware method is called.
Subsequent calls reuse the cache.

## WireGuard client

```python
configs = await client.wg_client.get_wireguard_clients()
# [
#   {"name": "Home/group-1/peer-1", "group_id": 1, "peer_id": 1, "tunnel_id": …},
#   …
# ]

state = await client.wg_client.get_wireguard_state()
# [{"name": "group/peer", "status": 1, "tunnel_id": …}, …]

await client.wg_client.start_wireguard_client(group_id=1, peer_id=1)
await client.wg_client.stop_wireguard_client(group_id=1, peer_id=1)
```

`get_wireguard_clients()` returns one entry per WireGuard peer. The
`name` is the human-readable label (`<group>/<peer>`); the integer IDs
are what you pass to `start_/stop_wireguard_client`.

## OpenVPN client

The OpenVPN client is structured around two layers:

- A legacy `OvpnModule` (`client.ovpn_client.ovpn_legacy`) that talks to
  the firmware 4.8 `ovpn-client` aggregate endpoints.
- A shared `VpnClientModule` (`client.ovpn_client.vpn_client`) that
  talks to the unified `vpn-client` tunnel state.

`OvpnClientModule.get_ovpn_clients()` reconciles both layers and returns
a list of merged config dicts that include `tunnel_id` (or `None` if the
router has no OpenVPN tunnel configured).

```python
configs = await client.ovpn_client.get_ovpn_clients()
status = await client.ovpn_client.get_status()       # List of state dicts
await client.ovpn_client.start(group_id=1, client_id=1)
await client.ovpn_client.stop(group_id=1, client_id=1)
```

If no tunnel is configured, `start()` raises `ValueError("No OpenVPN
tunnel found to start connection")`. `stop()` is a no-op in the same
situation.

## WireGuard server

```python
status = await client.wg_server.get_status()       # dict
peers = await client.wg_server.get_peer_list()      # list of peer dicts
await client.wg_server.start()
await client.wg_server.stop()
await client.wg_server.set_config(
    address_v4="10.0.0.1/24",
    port=51820,
    address_v6="fd00::1/64",   # optional
    private_key="…",           # optional
)
await client.wg_server.add_peer(name="laptop", public_key="…", allowed_ips="…")
await client.wg_server.remove_peer(peer_id=1, remove_all=False)
await client.wg_server.set_peer(peer_id=1, name="laptop-renamed")
```

`add_peer` and `set_peer` accept any additional keyword arguments; the
router ignores unknown keys and the library forwards them as-is.

## OpenVPN server

```python
status = await client.ovpn_server.get_status()
config = await client.ovpn_server.get_config()
users = await client.ovpn_server.get_user_list()
await client.ovpn_server.start()
await client.ovpn_server.stop()
```

## See also

- [Architecture](architecture.md) — how `_is_firmware_at_least` works.
- [Errors](errors.md) — what happens when a peer id does not exist.
