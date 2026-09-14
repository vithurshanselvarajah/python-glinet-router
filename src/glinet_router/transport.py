"""HTTP transport abstraction.

The library defaults to an :class:`aiohttp.ClientSession`, but the
transport is abstracted so consumers can:

- Pass a session they already own (the long-running HA case).
- Inject a mock for tests.
- Plug in an alternative HTTP library.
- Use a synchronous transport from a CLI script.

The transport is responsible only for issuing the request and returning
the raw response object. Status code and JSON-RPC envelope decoding
happen in :func:`glinet.client._extract_response_data`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Protocol


class HttpTransport(Protocol):
    """Minimal async transport interface used by :class:`GLinetApiClient`.

    Implementations must:
    - accept a JSON body as a dict,
    - return an object with a ``.json()`` coroutine and a ``.status``
      attribute, OR raise a transport-level exception,
    - raise any underlying-library exception on a transport failure
      (timeout, DNS, connection refused, etc.).

    The default implementation is :class:`AiohttpTransport`.
    """

    def post(self, url: str, json: dict[str, Any]) -> AsyncIterator[Any]: ...


class AiohttpTransport:
    """Wrap an :class:`aiohttp.ClientSession` as an :class:`HttpTransport`.

    Use this when you want the library to own the session lifecycle, or
    when you want to swap in a custom session (with a custom connector, a
    cookie jar, etc.).
    """

    def __init__(self, session: Any, ssl: bool | None = None) -> None:
        self._session = session
        self._ssl = ssl

    @asynccontextmanager
    async def post(self, url: str, json: dict[str, Any]) -> AsyncIterator[Any]:
        async with self._session.post(
            url,
            json=json,
            ssl=self._ssl,  # type: ignore[arg-type]
        ) as response:
            yield response


__all__ = ["AiohttpTransport", "HttpTransport"]
