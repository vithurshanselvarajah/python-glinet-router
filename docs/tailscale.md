# Tailscale

The `client.tailscale` module wraps the `tailscale` JSON-RPC endpoints.
It is built around a small state machine that maps the router's
connection status to the [`TailscaleConnection`](../src/glinet/models.py)
enum.

## Connection states

```python
from glinet import TailscaleConnection

TailscaleConnection.DISCONNECTED              # 0
TailscaleConnection.LOGIN_REQUIRED            # 1
TailscaleConnection.AUTHORIZATION_REQUIRED    # 2
TailscaleConnection.CONNECTED                 # 3
TailscaleConnection.CONNECTING                # 4
```

`get_connection()` calls `tailscale/get_status` and returns the matching
enum member. `get_status()` returns the raw dict or list (depending on
firmware) if you need access to the underlying payload.

## Configuring and reading state

```python
config = await client.tailscale.get_config()      # dict — full Tailscale config
status = await client.tailscale.get_status()      # dict | list — raw status

# Update the running config. Only known keys are meaningful; unknown keys
# are forwarded as-is.
await client.tailscale.set_config({"enabled": True, "accept_routes": True})
```

`is_configured()` returns `True` if either a status or a config is
available, `False` if the router reports the feature is not present
(or both calls raise `APIClientError`). `get_details()` returns a
combined payload:

```python
{
    "config": { ... },
    "connection": TailscaleConnection.CONNECTED,
}
```

or `None` if the feature is not configured.

## `connect` / `disconnect`

`connect()` and `disconnect()` are higher-level helpers that retry until
the router reaches the target state. They raise:

- `ConnectionError` after 10 unsuccessful retries.
- `ConnectionAbortedError` if the router reports `LOGIN_REQUIRED` or
  `AUTHORIZATION_REQUIRED` — the user must complete the OAuth flow on
  the router's web UI before either can succeed.

```python
try:
    await client.tailscale.connect()
except ConnectionAbortedError:
    # User needs to log in to Tailscale on the router's admin page.
    ...
except ConnectionError:
    # Give up after the retry loop; surface to the operator.
    ...
```

The retry loop sleeps 0.3 seconds between attempts and 3 seconds when
the router reports `CONNECTING` (so we give it time to finish the
handshake).

## See also

- [Models](../src/glinet/models.py) — `TailscaleConnection` enum.
- [Errors](errors.md) — what `APIClientError` means for the
  `is_configured()` probe.
