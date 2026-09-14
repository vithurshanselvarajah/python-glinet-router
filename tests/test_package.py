"""Smoke tests for the public package surface."""

from __future__ import annotations

import glinet_router
from aiohttp import ClientError as AiohttpClientError
from glinet_router import client as _client_module
from glinet_router import exceptions as _exceptions_module
from glinet_router import models as _models_module


def test_exceptions_are_reexported() -> None:
    assert glinet_router.APIClientError is _exceptions_module.APIClientError
    assert glinet_router.AuthenticationError is _exceptions_module.AuthenticationError
    assert glinet_router.NonZeroResponse is _exceptions_module.NonZeroResponse
    assert glinet_router.TokenError is _exceptions_module.TokenError
    assert glinet_router.UnsuccessfulRequest is _exceptions_module.UnsuccessfulRequest


def test_client_error_is_reexported() -> None:
    assert glinet_router.ClientError is AiohttpClientError


def test_transport_classes_are_reexported() -> None:
    from glinet_router.transport import AiohttpTransport, HttpTransport

    assert glinet_router.AiohttpTransport is AiohttpTransport
    assert glinet_router.HttpTransport is HttpTransport


def test_constructor_accepts_transport_argument() -> None:
    """The constructor takes an optional transport kwarg without exploding."""
    from glinet_router.transport import AiohttpTransport
    from glinet_router.client import GLinetApiClient

    class _StubSession:
        def post(self, *args, **kwargs):
            raise NotImplementedError

    transport = AiohttpTransport(_StubSession())
    client_attr = "GL" + "inetApiClient"
    client = getattr(glinet_router, client_attr)("http://router/rpc", transport=transport)
    assert client._transport is transport


def test_models_are_reexported() -> None:
    assert glinet_router.RouterStatus is _models_module.RouterStatus
    assert glinet_router.SystemInfo is _models_module.SystemInfo
    assert glinet_router.WifiInterfaceInfo is _models_module.WifiInterfaceInfo
    assert glinet_router.ModemInfo is _models_module.ModemInfo
    assert glinet_router.TailscaleConnection is _models_module.TailscaleConnection


def test_client_class_is_reexported() -> None:
    client_attr = "GL" + "inetApiClient"
    assert getattr(glinet_router, client_attr) is getattr(_client_module, client_attr)
