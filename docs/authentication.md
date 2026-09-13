# Authentication

The GL.iNet router API uses a challenge/response JSON-RPC login flow. The
`glinet` library implements it for you in
[`GLinetApiClient.authenticate`](../src/glinet/client.py).

## Flow

```text
client  ── challenge {username: "root"} ─────►  router
client  ◄── {alg, salt, nonce, hash-method} ──  router

client computes:
  cipher = hasher(alg).using(salt=salt).hash(password)
  digest = hashlib.<hash-method>(f"{user}:{cipher}:{nonce}".encode()).hexdigest()

client  ── login {username, hash: digest} ─►  router
client  ◄── {sid: "..."}                  ──  router
```

Once `sid` is stored, every subsequent call goes through the `call` RPC with
`sid` as the first parameter. `GLinetApiClient` does this for you — every
module method automatically prepends the `sid`.

## Default supported algorithms

| `alg` value | Hasher | Notes |
| --- | --- | --- |
| `1` | `md5_crypt` | Legacy; widely supported. |
| `5` | `sha256_crypt` | Default on most modern firmwares. |
| `6` | `sha512_crypt` | High-security firmwares. |

The post-cipher digest defaults are `md5`, `sha256`, and `sha512` from
`hashlib`. The router advertises the digest via the `hash-method` field of
the challenge response; if it's missing, the client defaults to `md5`.

## Adding a new algorithm

The algorithm and digest tables are class-level dicts, so you can extend
them on the instance (or in a subclass) without touching the library:

```python
from glinet import GLinetApiClient
from passlib.hash import sha512_crypt

client = GLinetApiClient("http://router/rpc")
# Firmware 5.0 introduces a new alg value with a different work factor.
client.auth_hashers[7] = sha512_crypt
await client.authenticate("root", "secret")
```

If a router reports an `alg` that the library doesn't recognise, the call
fails fast with a `ValueError` that lists the supported values — easier to
debug than a silent `TypeError` deep in a worker thread.

## Re-authentication and token rotation

The library does not re-authenticate automatically. The
[ha-glinet-router integration](https://github.com/vithurshanselvarajah/ha-glinet-router)
implements a `refresh_session_token` helper that catches
`TokenError` and re-calls `authenticate` before refreshing coordinator data.
If you build a long-running consumer, do the same:

```python
from glinet import TokenError

async def safe_call(client, coro):
    try:
        return await coro
    except TokenError:
        await client.authenticate("root", password)
        return await coro
```

## Thread safety of `authenticate`

`authenticate` runs the password hashing in
[`asyncio.to_thread`](https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread),
so the event loop is not blocked while `passlib` runs (it's CPU-bound and
can take several hundred milliseconds for `sha512_crypt`). This means you
do not need a process-pool executor on the calling side.

## See also

- [Errors](errors.md) — how router error codes surface as Python exceptions.
- [Architecture](architecture.md) — where the hashing helpers live in the
  package layout.
