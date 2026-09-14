# Errors

`glinet` raises a small hierarchy of exceptions so consumers can decide
between "retry later", "ask for a new password", and "give up". Every
exception inherits from `APIClientError`, so a single `except
APIClientError` clause is enough to catch anything raised by the library.

## Exception hierarchy

```
APIClientError
├── NonZeroResponse
│   └── AuthenticationError
│       └── TokenError
└── UnsuccessfulRequest
```

| Exception | When it is raised | Suggested reaction |
| --- | --- | --- |
| `APIClientError` | Base class. Catch this to handle every library error. | Inspect subclass. |
| `NonZeroResponse` | The router returned a JSON-RPC payload with `error.code < 0`. | Log and retry, or surface to the user. |
| `AuthenticationError` | `error.code == -32000`. The router rejected the credentials or the current session. | Ask the user for a new password, then call `authenticate` again. |
| `TokenError` | `error.code == -1`. The session token expired or is invalid. | Re-`authenticate` and retry the call. |
| `UnsuccessfulRequest` | Transport-level failure: HTTP non-2xx, invalid JSON, network error. | Retry with backoff. |
| `ValueError` | Router returned an unsupported `alg` or `hash-method` during `authenticate`. | Override `auth_hashers` / `auth_digests` and retry. |
| `TypeError` | `custom_call("challenge", …)` or `custom_call("login", …)` was passed a non-dict `params`. | Pass a dict. |

The integration's `hub.py` translates `TokenError` into a
`ConfigEntryAuthFailed` so Home Assistant shows the reauth flow.

## Router error code mapping

| Router `error.code` | Exception |
| --- | --- |
| `-1` | `TokenError` |
| `-32000` | `AuthenticationError` |
| Any other negative code | `NonZeroResponse` |

The error code is included in the exception message, so a log line
looks like:

```
glinet.exceptions.TokenError: Request returned error code -1 (Session expired)
```

## Re-exports

For convenience, `glinet` re-exports `aiohttp.ClientError` as
`glinet.ClientError`. This lets you write a single `except` block that
covers both library and transport errors:

```python
from glinet_router import APIClientError, ClientError

try:
    await client.system.get_info()
except TokenError:
    await client.authenticate("root", password)
except APIClientError:
    # Library-level failure (router error, etc.)
    ...
except ClientError:
    # Transport-level failure (network down, DNS, etc.)
    ...
```

## See also

- [Authentication](authentication.md) — what `authenticate` does when the
  router reports a new algorithm.
- [Architecture](architecture.md) — how `_extract_response_data` builds
  the exception from the JSON-RPC payload.
