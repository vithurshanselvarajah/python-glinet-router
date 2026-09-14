from __future__ import annotations

from typing import TYPE_CHECKING, Any

from glinet_router.const import DEFAULT_TIMEOUT

if TYPE_CHECKING:
    from glinet_router.client import GLinetApiClient


class BaseModule:
    def __init__(self, client: GLinetApiClient) -> None:
        self._client = client

    async def _call(
        self,
        module: str,
        method: str,
        params: dict[str, Any] | list[Any] | None = None,
        timeout_seconds: int = DEFAULT_TIMEOUT,
    ) -> Any:
        if params is None:
            params = {}
        payload = self._client._build_sid_payload(
            "call", [module, method, params], self._client.sid
        )
        return await self._client._send_request(payload, timeout_seconds=timeout_seconds)
