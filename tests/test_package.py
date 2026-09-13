"""Smoke tests for the public package surface."""

from __future__ import annotations

import glinet
from aiohttp import ClientError as AiohttpClientError
from glinet import client as _client_module
from glinet import exceptions as _exceptions_module
from glinet import models as _models_module


def test_exceptions_are_reexported() -> None:
    assert glinet.APIClientError is _exceptions_module.APIClientError
    assert glinet.AuthenticationError is _exceptions_module.AuthenticationError
    assert glinet.NonZeroResponse is _exceptions_module.NonZeroResponse
    assert glinet.TokenError is _exceptions_module.TokenError
    assert glinet.UnsuccessfulRequest is _exceptions_module.UnsuccessfulRequest


def test_client_error_is_reexported() -> None:
    assert glinet.ClientError is AiohttpClientError


def test_transport_classes_are_reexported() -> None:
    from glinet.transport import AiohttpTransport, HttpTransport

    assert glinet.AiohttpTransport is AiohttpTransport
    assert glinet.HttpTransport is HttpTransport


def test_constructor_accepts_transport_argument() -> None:
    """The constructor takes an optional transport kwarg without exploding."""
    from glinet.transport import AiohttpTransport
    from glinet.client import GLinetApiClient

    class _StubSession:
        def post(self, *args, **kwargs):
            raise NotImplementedError

    transport = AiohttpTransport(_StubSession())
    client_attr = "GL" + "inetApiClient"
    client = getattr(glinet, client_attr)("http://router/rpc", transport=transport)
    assert client._transport is transport


def test_models_are_reexported() -> None:
    assert glinet.RouterStatus is _models_module.RouterStatus
    assert glinet.SystemInfo is _models_module.SystemInfo
    assert glinet.WifiInterfaceInfo is _models_module.WifiInterfaceInfo
    assert glinet.ModemInfo is _models_module.ModemInfo
    assert glinet.TailscaleConnection is _models_module.TailscaleConnection


def test_client_class_is_reexported() -> None:
    client_attr = "GL" + "inetApiClient"
    assert getattr(glinet, client_attr) is getattr(_client_module, client_attr)
