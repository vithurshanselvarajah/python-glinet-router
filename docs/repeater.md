# Repeater

The `client.repeater` module covers GL.iNet's repeater mode: scanning
for nearby Wi-Fi networks, connecting to one, listing saved networks,
and the "bare mode" entry/exit endpoints.

## Reading state

```python
status = await client.repeater.get_status()       # current mode + connection
config = await client.repeater.get_config()       # repeater config dict
await client.repeater.set_config({"enabled": True, "ssid": "…"})
```

`get_config` may return `{}` if the router is not currently in repeater
mode; that's a router feature, not a library error.

## Scanning for networks

```python
networks = await client.repeater.scan({"duration": 10})
# [
#   {"ssid": "Home Wi-Fi", "bssid": "…", "signal": -55, "encryption": "psk2", …},
#   …
# ]
```

The `duration` parameter is forwarded to the router and controls how
long the scan runs. Internally, `scan()` uses `SCAN_TIMEOUT` (30s) for
the HTTP request so it doesn't trip the default 2s timeout.

## Connecting / disconnecting

```python
await client.repeater.connect({"ssid": "Home Wi-Fi", "password": "…", …})
await client.repeater.disconnect()
```

`connect()` uses `LONG_TIMEOUT` (5s) for the HTTP request because the
router can take a few seconds to complete the association.

## Bare mode

```python
await client.repeater.enter_bare_mode()
await client.repeater.exit_bare_mode()
```

These toggle whether the router acts as a transparent bridge or as a
router on its repeater uplink. Most users never need them.

## Saved AP management

```python
saved = await client.repeater.get_saved_ap_list()
# [{"ssid": "Home Wi-Fi", "password": "…"}, …]

await client.repeater.remove_saved_ap(ssid="Home Wi-Fi")
```

## Channel prompts

```python
prompt = await client.repeater.get_channel_prompt()
await client.repeater.set_channel_prompt({"channel": 6, "auto": False})
```

Some firmwares ask the user to pick a channel before completing the
association; these endpoints let a host application do that
programmatically.

## See also

- [Architecture](architecture.md) — how module methods use longer
  timeouts for slow operations.
