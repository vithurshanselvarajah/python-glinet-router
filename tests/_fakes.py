"""Shared test doubles for the GL.iNet JSON-RPC client.

These helpers are used by the unit tests in this package. They implement just
enough of the `aiohttp` `ClientSession` surface to let the client's request
code path run without making real network calls.
"""

from __future__ import annotations

from typing import Any


class FakeResponse:
    def __init__(
        self,
        payload: dict[str, Any] | list[Any] | Exception,
        status: int = 200,
        text: str = "not-json",
    ) -> None:
        self._payload = payload
        self.status = status
        self._text = text

    async def json(self, content_type: str | None = None) -> dict[str, Any] | list[Any]:
        assert content_type is None
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload

    async def text(self) -> str:
        return self._text


class FakePostContext:
    def __init__(self, response: FakeResponse) -> None:
        self._response = response

    async def __aenter__(self) -> FakeResponse:
        return self._response

    async def __aexit__(self, *_: Any) -> None:
        return None


class FakeSession:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def post(
        self, url: str, json: dict[str, Any], timeout: int, ssl: Any = None
    ) -> FakePostContext:
        self.requests.append({"url": url, "json": json, "timeout": timeout, "ssl": ssl})
        payload = self.responses.pop(0)
        if isinstance(payload, FakeResponse):
            return FakePostContext(payload)
        return FakePostContext(FakeResponse(payload))
