"""Async client for the GL.iNet router JSON-RPC API."""

from aiohttp import ClientError

from .client import GLinetApiClient
from .exceptions import (
    APIClientError,
    AuthenticationError,
    NonZeroResponse,
    TokenError,
    UnsuccessfulRequest,
)
from .models import (
    ModemInfo,
    RouterStatus,
    SystemInfo,
    TailscaleConnection,
    WifiInterfaceInfo,
)
from .transport import AiohttpTransport, HttpTransport

__all__ = [
    "APIClientError",
    "AiohttpTransport",
    "AuthenticationError",
    "ClientError",
    "GLinetApiClient",
    "HttpTransport",
    "ModemInfo",
    "NonZeroResponse",
    "RouterStatus",
    "SystemInfo",
    "TailscaleConnection",
    "TokenError",
    "UnsuccessfulRequest",
    "WifiInterfaceInfo",
]
