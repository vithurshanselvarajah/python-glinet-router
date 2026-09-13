from __future__ import annotations

import asyncio
import hashlib
import re
from typing import Any

from aiohttp import ClientResponse, ClientResponseError, ClientSession

from .const import (
    DEFAULT_TIMEOUT,
    LONG_TIMEOUT,
)
from .transport import AiohttpTransport, HttpTransport
from .exceptions import (
    APIClientError,
    AuthenticationError,
    NonZeroResponse,
    TokenError,
    UnsuccessfulRequest,
)
from .modules import (
    AdGuardModule,
    BlackWhiteListModule,
    ClientsModule,
    DiagModule,
    FanModule,
    FirewallModule,
    KmwanModule,
    LedModule,
    MacCloneModule,
    McuModule,
    ModemModule,
    Mwan3Module,
    OvpnClientModule,
    OvpnServerModule,
    ParentalControlModule,
    RepeaterModule,
    SystemModule,
    TailscaleModule,
    UpgradeModule,
    WgClientModule,
    WgServerModule,
    WifiModule,
    ZeroTierModule,
)


def _decode_firmware_version(version: str) -> tuple[int, int, int, int]:
    numbers: list[int] = [int(value) for value in re.findall(r"\d+", version)]
    normalized: list[int] = [*numbers, 0, 0, 0, 0][:4]
    return tuple(normalized)  # type: ignore[return-value]


async def _extract_response_data(response: ClientResponse) -> Any:
    try:
        payload = await response.json(content_type=None)
    except (ValueError, ClientResponseError) as exc:
        text = await response.text()
        raise UnsuccessfulRequest(
            f"Request failed or returned invalid JSON (status {response.status}): {text}"
        ) from exc

    if not 200 <= response.status < 300:
        raise UnsuccessfulRequest(f"Request failed with status {response.status}: {payload}")

    if "result" in payload:
        return payload["result"]

    if "error" not in payload:
        raise APIClientError(f"Unexpected response from GL.iNet router: {payload}")

    error = payload["error"]
    message = error.get("message", "null")
    code = error.get("code", 0)

    if code == -1:
        raise TokenError(f"Request returned error code -1 ({message})")
    if code == -32000:
        raise AuthenticationError(f"Request returned error code -32000 ({message})")
    if code < 0:
        raise NonZeroResponse(f"Request returned error code {code} with message: {message}")

    return payload


class GLinetApiClient:
    _firmware_version: tuple[int, int, int, int] | None = None

    # Mapping of GL.iNet "alg" values to passlib hashers. Populated lazily
    # on the first call to `authenticate` so that callers using only the
    # read-only API (or pre-existing sessions) do not have to install
    # `passlib`. Extend at runtime to add new firmware variants.
    auth_hashers: dict[int, Any] = {}

    # Mapping of GL.iNet "hash-method" values to hashlib constructors.
    # `hashlib` is always available, so this table is populated eagerly.
    auth_digests: dict[str, Any] = {
        "md5": hashlib.md5,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512,
    }

    def __init__(
        self,
        base_url: str,
        session: ClientSession | None = None,
        sid: str | None = None,
        verify_ssl: bool = False,
        transport: HttpTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._ssl_setting = None if verify_ssl else False
        if transport is not None:
            # Caller-supplied transport takes precedence over the session.
            self._owns_session = False
            self._session: ClientSession | None = None
            self._transport: HttpTransport = transport
        elif session is not None:
            self._owns_session = False
            self._session = session
            self._transport = AiohttpTransport(
                session, ssl=None if verify_ssl else False
            )
        else:
            self._owns_session = True
            self._session = ClientSession()
            self._transport = AiohttpTransport(
                self._session, ssl=None if verify_ssl else False
            )
        self.sid = sid
        self._logged_in = sid is not None

        self.system = SystemModule(self)
        self.modem = ModemModule(self)
        self.mcu = McuModule(self)
        self.kmwan = KmwanModule(self)
        self.mwan3 = Mwan3Module(self)
        self.wifi = WifiModule(self)
        self.zerotier = ZeroTierModule(self)
        self.clients = ClientsModule(self)
        self.wg_client = WgClientModule(self)
        self.wg_server = WgServerModule(self)
        self.ovpn_client = OvpnClientModule(self)
        self.ovpn_server = OvpnServerModule(self)
        self.tailscale = TailscaleModule(self)
        self.repeater = RepeaterModule(self)
        self.upgrade = UpgradeModule(self)
        self.fan = FanModule(self)
        self.firewall = FirewallModule(self)
        self.led = LedModule(self)
        self.macclone = MacCloneModule(self)
        self.diag = DiagModule(self)
        self.adguard = AdGuardModule(self)
        self.parental_control = ParentalControlModule(self)
        self.black_white_list = BlackWhiteListModule(self)

    @staticmethod
    def _build_sid_payload(method: str, params: list[Any], sid: str | None) -> dict[str, Any]:
        return {
            "method": method,
            "jsonrpc": "2.0",
            "params": [sid, *params],
            "id": 0,
        }

    @staticmethod
    def _build_payload(method: str, params: dict[str, Any]) -> dict[str, Any]:
        return {
            "method": method,
            "jsonrpc": "2.0",
            "params": params,
            "id": 0,
        }

    async def __aenter__(self) -> GLinetApiClient:
        """Return self for use as an async context manager.

        When the client was constructed without a session, the underlying
        :class:`aiohttp.ClientSession` is created here and closed on exit.
        When a session was supplied, the caller still owns it.
        """
        return self

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying session if this client owns it."""
        if self._owns_session and not self._session.closed:
            await self._session.close()

    async def _ensure_firmware_version(self) -> None:
        if self._firmware_version is None:
            await self.system.get_info()

    async def _is_firmware_at_least(self, version: tuple[int, int, int, int]) -> bool:
        await self._ensure_firmware_version()
        fw_ver = self._firmware_version
        return fw_ver is not None and fw_ver >= version

    async def _send_request(
        self, payload: dict[str, Any], timeout_seconds: int = DEFAULT_TIMEOUT
    ) -> Any:
        # The transport is responsible for the HTTP-level concerns
        # (timeouts, ssl, connector) at construction time; the body is
        # all this call site needs to provide.
        async with self._transport.post(
            self._base_url,
            json=payload,
        ) as response:
            return await _extract_response_data(response)

    async def _request_challenge(self, username: str) -> dict[str, Any]:
        result = await self._send_request(
            self._build_payload("challenge", {"username": username}),
            timeout_seconds=LONG_TIMEOUT,
        )
        return dict(result)

    async def _fetch_session_id(self, username: str, login_hash: str) -> dict[str, Any]:
        result = await self._send_request(
            self._build_payload("login", {"username": username, "hash": login_hash}),
            timeout_seconds=LONG_TIMEOUT,
        )
        return dict(result)

    async def is_router_reachable(self, username: str = "root") -> bool:
        try:
            return bool(await self._request_challenge(username))
        except APIClientError:
            return False

    def _ensure_default_hashers(self) -> None:
        """Populate `auth_hashers` with the built-in `passlib` mappings.

        Importing `passlib` is deferred to here so consumers who only use the
        library for read-only calls (or with a pre-existing sid) do not need
        to install it. Install the `[auth]` extra to enable this.
        """
        if self.auth_hashers:
            return
        try:
            from passlib.hash import (  # type: ignore[import-untyped]
                md5_crypt,
                sha256_crypt,
                sha512_crypt,
            )
        except ImportError as exc:
            raise ImportError(
                "passlib is required for GLinetApiClient.authenticate(). "
                "Install it with `pip install 'glinet[auth]'` or "
                "`pip install passlib>=1.7.4`."
            ) from exc
        self.auth_hashers.update(
            {1: md5_crypt, 5: sha256_crypt, 6: sha512_crypt}
        )

    async def authenticate(self, username: str, password: str) -> None:
        self._ensure_default_hashers()

        def _compute_hash(
            algorithm: int,
            salt: str,
            nonce: str,
            hash_method: str,
            login_username: str,
            login_password: str,
        ) -> str:
            hasher = self.auth_hashers.get(algorithm)
            if hasher is None:
                supported = ", ".join(str(k) for k in self.auth_hashers)
                raise ValueError(
                    f"Unsupported router cipher algorithm {algorithm!r}. "
                    f"Supported: {supported}. Override GLinetApiClient.auth_hashers "
                    "to add a new one."
                )

            cipher_password = hasher.using(salt=salt).hash(login_password)

            digest = self.auth_digests.get(hash_method)
            if digest is None:
                supported = ", ".join(self.auth_digests)
                raise ValueError(
                    f"Unsupported router hash method {hash_method!r}. "
                    f"Supported: {supported}. Override GLinetApiClient.auth_digests "
                    "to add a new one."
                )

            data = f"{login_username}:{cipher_password}:{nonce}".encode()
            return digest(data, usedforsecurity=False).hexdigest()

        challenge = await self._request_challenge(username)
        login_hash = await asyncio.to_thread(
            _compute_hash,
            challenge["alg"],
            challenge["salt"],
            challenge["nonce"],
            challenge.get("hash-method", "md5"),
            username,
            password,
        )
        response = await self._fetch_session_id(username, login_hash)
        if "sid" not in response:
            raise AuthenticationError("Router login response did not include a session id")
        self.sid = str(response["sid"])
        self._logged_in = True

    @property
    def logged_in(self) -> bool:
        return self._logged_in

    async def custom_call(
        self, method: str, params: dict[str, Any] | list[Any] | None = None
    ) -> dict[str, Any] | list[Any]:
        if params is None:
            params = {}
        if "/" in method:
            module, _, sub_method = method.partition("/")
            payload = self._build_sid_payload("call", [module, sub_method, params], self.sid)
        elif method == "call":
            if isinstance(params, list):
                payload = self._build_sid_payload("call", params, self.sid)
            else:
                payload = self._build_sid_payload("call", [params], self.sid)
        elif method in ("challenge", "login"):
            if not isinstance(params, dict):
                raise TypeError(
                    f"{method!r} expects a dict of parameters, got {type(params).__name__}"
                )
            payload = self._build_payload(method, params)
        else:
            if isinstance(params, list):
                payload = self._build_sid_payload(method, params, self.sid)
            else:
                payload = self._build_sid_payload(method, [params], self.sid)
        return await self._send_request(payload)
