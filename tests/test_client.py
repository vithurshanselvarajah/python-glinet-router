from typing import Any

import pytest

from glinet.client import (
    GLinetApiClient,
    _extract_response_data,
)
from glinet.exceptions import (
    APIClientError,
    AuthenticationError,
    NonZeroResponse,
    TokenError,
    UnsuccessfulRequest,
)
from glinet.models import WifiInterfaceInfo

from tests._fakes import FakeResponse, FakeSession


async def test_extract_response_data_returns_result() -> None:
    response = FakeResponse({"jsonrpc": "2.0", "result": {"ok": True}, "id": 0})

    assert await _extract_response_data(response) == {"ok": True}


@pytest.mark.parametrize(
    ("code", "exception"),
    [
        (-1, TokenError),
        (-32000, AuthenticationError),
        (-32001, NonZeroResponse),
    ],
)
async def test_extract_response_data_maps_router_errors(
    code: int,
    exception: type[Exception],
) -> None:
    response = FakeResponse({"jsonrpc": "2.0", "error": {"code": code, "message": "nope"}})

    with pytest.raises(exception):
        await _extract_response_data(response)


async def test_extract_response_data_rejects_http_errors() -> None:
    response = FakeResponse({"error": {"code": 500}}, status=500)

    with pytest.raises(UnsuccessfulRequest):
        await _extract_response_data(response)


async def test_extract_response_data_rejects_invalid_json() -> None:
    response = FakeResponse(ValueError("bad json"), text="<html>bad</html>")

    with pytest.raises(UnsuccessfulRequest):
        await _extract_response_data(response)


async def test_extract_response_data_rejects_unexpected_payload_shape() -> None:
    response = FakeResponse({"jsonrpc": "2.0", "id": 0})

    with pytest.raises(APIClientError):
        await _extract_response_data(response)


async def test_get_online_clients_filters_offline_clients() -> None:
    session = FakeSession(
        [
            {
                "result": {
                    "clients": [
                        {"mac": "aa:aa:aa:aa:aa:aa", "online": True, "name": "phone"},
                        {"mac": "bb:bb:bb:bb:bb:bb", "online": False, "name": "laptop"},
                    ]
                }
            }
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")

    assert await client.clients.get_online() == {
        "aa:aa:aa:aa:aa:aa": {"mac": "aa:aa:aa:aa:aa:aa", "online": True, "name": "phone"}
    }


async def test_repeater_advanced_methods_use_expected_payloads() -> None:
    session = FakeSession(
        [
            {"result": None},
            {"result": None},
            {"result": {"chan_prompt_en": True, "popup_prompt_en": False}},
            {"result": None},
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")

    assert await client.repeater.enter_bare_mode() == {}
    assert await client.repeater.exit_bare_mode() == {}
    assert await client.repeater.get_channel_prompt() == {
        "chan_prompt_en": True,
        "popup_prompt_en": False,
    }
    assert await client.repeater.set_channel_prompt({"chan_prompt_en": False}) == {}

    assert [request["json"]["params"] for request in session.requests] == [
        ["sid-1", "repeater", "enter_bare_mode", {}],
        ["sid-1", "repeater", "exit_bare_mode", {}],
        ["sid-1", "repeater", "get_channel_prompt", {}],
        ["sid-1", "repeater", "set_channel_prompt", {"chan_prompt_en": False}],
    ]


async def test_repeater_scan_and_connect_use_documented_payloads() -> None:
    session = FakeSession(
        [
            {"result": {"res": [{"ssid": "SecuredNet"}]}},
            {"result": None},
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")

    assert await client.repeater.scan({"refresh": True}) == [{"ssid": "SecuredNet"}]
    assert (
        await client.repeater.connect(
            {
                "ssid": "SecuredNet",
                "key": "secret-pass",
                "remember": True,
                "manual": False,
                "protocol": "dhcp",
                "disguise": False,
                "auto_portal": False,
            }
        )
        == {}
    )

    assert [request["json"]["params"] for request in session.requests] == [
        ["sid-1", "repeater", "scan", {"refresh": True}],
        [
            "sid-1",
            "repeater",
            "connect",
            {
                "ssid": "SecuredNet",
                "key": "secret-pass",
                "remember": True,
                "manual": False,
                "protocol": "dhcp",
                "disguise": False,
                "auto_portal": False,
            },
        ],
    ]


async def test_get_wifi_interfaces_returns_models() -> None:
    session = FakeSession(
        [
            {
                "result": {
                    "res": [
                        {
                            "ifaces": [
                                {
                                    "name": "wlan0",
                                    "ssid": "Main",
                                    "key": "secret",
                                    "enabled": True,
                                    "encryption": "psk2",
                                },
                                {"ssid": "Missing name", "key": "secret"},
                            ]
                        }
                    ]
                }
            }
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")

    assert await client.wifi.get_interfaces() == {
        "wlan0": WifiInterfaceInfo(
            enabled=True, ssid="Main", guest=False, hidden=False, encryption="psk2"
        )
    }


async def test_sms_methods_use_sms_module_payloads() -> None:
    session = FakeSession(
        [
            {"result": {"list": [{"name": "sms-1", "body": "hello"}]}},
            {"result": {"sent": True}},
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")
    client._firmware_version = (4, 7, 0, 0)

    assert await client.modem.get_sms_list() == [{"name": "sms-1", "body": "hello"}]
    assert await client.modem.send_sms("1-1", "+441234567890", "hi") == {"sent": True}

    assert session.requests[0]["json"]["params"] == ["sid-1", "modem", "get_sms_list", {}]
    assert session.requests[1]["json"]["params"] == [
        "sid-1",
        "modem",
        "send_sms",
        {
            "bus": "1-1",
            "phone_number": "+441234567890",
            "body": "hi",
            "timeout": 10,
        },
    ]


async def test_send_sms_includes_slot_when_supplied() -> None:
    session = FakeSession([{"result": {"sent": True}}])
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")

    assert await client.modem.send_sms("cpu", "+441234567890", "hi", slot=2) == {"sent": True}

    assert session.requests[0]["json"]["params"] == [
        "sid-1",
        "modem",
        "send_sms",
        {
            "bus": "cpu",
            "phone_number": "+441234567890",
            "body": "hi",
            "timeout": 10,
            "slot": 2,
        },
    ]


async def test_get_modem_info_uses_documented_modem_endpoint() -> None:
    session = FakeSession([{"result": {"modems": [{"bus": "1-1"}]}}])
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")
    client._firmware_version = (4, 7, 0, 0)

    assert await client.modem.get_info() == {"modems": [{"bus": "1-1"}]}
    assert session.requests[0]["json"]["params"] == ["sid-1", "modem", "get_info", {}]


async def test_modem_status_uses_49_slot_endpoints_for_new_firmware() -> None:
    session = FakeSession(
        [
            {"result": {"interfaces": ["modem_cpu_s2"]}},
            {
                "result": {
                    "signals": [
                        {
                            "slot": 2,
                            "timestamp": 10,
                            "strength": 4,
                            "rsrp": -80,
                            "rsrq": -11,
                            "sinr": 25,
                            "network_type": "NR5G-SA",
                        }
                    ]
                }
            },
            {
                "result": {
                    "networks": [
                        {
                            "bus": "cpu",
                            "slot": "2",
                            "iccid": "iccid-2",
                            "status": 0,
                            "dial_status": 0,
                            "traffic_total": "1024",
                        }
                    ]
                }
            },
            {
                "result": {
                    "networks": [
                        {
                            "bus": "cpu",
                            "slot": "2",
                            "network_interface": "modem_cpu",
                            "ipv4": {"ip": "10.0.0.2"},
                            "ipv6": [],
                            "cell_info": {"mode": "NR5G-SA TDD", "band": 78},
                        }
                    ]
                }
            },
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")
    client._firmware_version = (4, 9, 0, 0)

    assert await client.modem.get_status() == {
        "modems": [
            {
                "bus": "cpu",
                "slot": "2",
                "iccid": "iccid-2",
                "status": 0,
                "dial_status": 0,
                "signal": 4,
                "network_type": "NR5G-SA",
                "simcard": {
                    "iccid": "iccid-2",
                    "network_type": "NR5G-SA",
                    "signal": {
                        "slot": 2,
                        "timestamp": 10,
                        "strength": 4,
                        "rsrp": -80,
                        "rsrq": -11,
                        "sinr": 25,
                        "network_type": "NR5G-SA",
                    },
                },
                "network": {"ipv4": {"ip": "10.0.0.2"}, "ipv6": {}},
                "cell_info": {"mode": "NR5G-SA TDD", "band": 78},
                "traffic_total": "1024",
                "protocol": None,
                "network_interface": "modem_cpu",
            }
        ]
    }
    assert [request["json"]["params"] for request in session.requests] == [
        ["sid-1", "modem", "get_modem_current_interface", {}],
        ["sid-1", "modem", "get_signals", {"time": 10}],
        ["sid-1", "modem", "get_network_status", {"bus": "cpu", "slot": 2}],
        ["sid-1", "modem", "get_network_info", {"bus": "cpu", "slot": 2}],
    ]


async def test_modem_sms_list_uses_49_bus_payload_for_new_firmware() -> None:
    session = FakeSession(
        [
            {"result": {"interfaces": ["modem_1_1_s1", "modem_1_1_2_s2"]}},
            {"result": {"list": [{"name": "sms-1", "bus": "1-1"}]}},
            {"result": {"list": [{"name": "sms-2", "bus": "1-1.2", "slot": 2}]}},
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")
    client._firmware_version = (4, 9, 0, 0)

    assert await client.modem.get_sms_list() == [
        {"name": "sms-1", "bus": "1-1"},
        {"name": "sms-2", "bus": "1-1.2", "slot": 2},
    ]
    assert [request["json"]["params"] for request in session.requests] == [
        ["sid-1", "modem", "get_modem_current_interface", {}],
        ["sid-1", "modem", "get_sms_list", {"bus": "1-1"}],
        ["sid-1", "modem", "get_sms_list", {"bus": "1-1.2"}],
    ]


async def test_get_kmwan_status_uses_kmwan_endpoint() -> None:
    session = FakeSession(
        [{"result": {"interfaces": [{"interface": "wan", "status_v4": 1, "status_v6": 0}]}}]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")

    assert await client.system.get_kmwan_status() == {
        "interfaces": [{"interface": "wan", "status_v4": 1, "status_v6": 0}]
    }
    assert session.requests[0]["json"]["params"] == [
        "sid-1",
        "kmwan",
        "get_status",
        {},
    ]


async def test_kmwan_methods_use_documented_payloads() -> None:
    session = FakeSession(
        [
            {"result": {"mode": 1, "interfaces": []}},
            {"result": {"interfaces": [{"interface": "wan", "status_v4": 0, "status_v6": 1}]}},
            {"result": None},
            {"result": None},
            {"result": None},
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")

    assert await client.kmwan.get_config() == {"mode": 1, "interfaces": []}
    assert await client.kmwan.get_status() == {
        "interfaces": [{"interface": "wan", "status_v4": 0, "status_v6": 1}]
    }
    assert await client.kmwan.set_config({"mode": 0, "interfaces": []}) == {}
    assert await client.kmwan.set_interface({"interface": "wan", "enable_check": True}) == {}
    assert await client.kmwan.set_sensitivity({"sensitivity": {"level": "custom", "val": 5}}) == {}

    assert [request["json"]["params"] for request in session.requests] == [
        ["sid-1", "kmwan", "get_config", {}],
        ["sid-1", "kmwan", "get_status", {}],
        ["sid-1", "kmwan", "set_config", {"mode": 0, "interfaces": []}],
        ["sid-1", "kmwan", "set_interface", {"interface": "wan", "enable_check": True}],
        [
            "sid-1",
            "kmwan",
            "set_sensitivity",
            {"sensitivity": {"level": "custom", "val": 5}},
        ],
    ]


async def test_upgrade_methods_use_documented_payloads() -> None:
    session = FakeSession(
        [
            {
                "result": {
                    "current_version": "4.0.0",
                    "version_new": "4.0.1",
                    "release_note": "Fixes and improvements",
                }
            },
            {"result": {"prompt": True, "upgrade_enable": False}},
            {"result": {"status": 1, "status_msg": "downloading", "percent": 42.5}},
            {"result": {"need_reboot_flag": True}},
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")

    assert await client.upgrade.check_firmware_online() == {
        "current_version": "4.0.0",
        "version_new": "4.0.1",
        "release_note": "Fixes and improvements",
    }
    assert await client.upgrade.get_config() == {"prompt": True, "upgrade_enable": False}
    assert await client.upgrade.get_online_upgrade_status() == {
        "status": 1,
        "status_msg": "downloading",
        "percent": 42.5,
    }
    assert await client.upgrade.upgrade_online(
        {
            "keep_config": True,
            "keep_package": False,
            "url": "http://example.invalid/fw.bin",
            "id": "fw-1",
            "size": 123,
            "sha256": "abc123",
        }
    ) == {"need_reboot_flag": True}

    assert [request["json"]["params"] for request in session.requests] == [
        ["sid-1", "upgrade", "check_firmware_online", {}],
        ["sid-1", "upgrade", "get_config", {}],
        ["sid-1", "upgrade", "get_online_upgrade_status", {}],
        [
            "sid-1",
            "upgrade",
            "upgrade_online",
            {
                "keep_config": True,
                "keep_package": False,
                "url": "http://example.invalid/fw.bin",
                "id": "fw-1",
                "size": 123,
                "sha256": "abc123",
            },
        ],
    ]


async def test_mwan3_methods_use_documented_payloads() -> None:
    session = FakeSession(
        [
            {"result": {"mode": 1, "interfaces": []}},
            {"result": {"interfaces": [{"interface": "wan", "status_v4": 0, "status_v6": 1}]}},
            {"result": None},
            {"result": None},
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")

    assert await client.mwan3.get_config() == {"mode": 1, "interfaces": []}
    assert await client.mwan3.get_status() == {
        "interfaces": [{"interface": "wan", "status_v4": 0, "status_v6": 1}]
    }
    assert await client.mwan3.set_config({"mode": 0, "flush_track": False}) == {}
    assert await client.mwan3.set_interface({"interface": "wan", "enable_check": True}) == {}

    assert [request["json"]["params"] for request in session.requests] == [
        ["sid-1", "mwan3", "get_config", {}],
        ["sid-1", "mwan3", "get_status", {}],
        ["sid-1", "mwan3", "set_config", {"mode": 0, "flush_track": False}],
        ["sid-1", "mwan3", "set_interface", {"interface": "wan", "enable_check": True}],
    ]


async def test_get_modem_info_extracts_nested_fields() -> None:
    session = FakeSession(
        [
            {"result": {"modems": [{"bus": "1-1", "model": "test-modem"}]}},
            {
                "result": {
                    "modems": [
                        {
                            "bus": "1-1",
                            "simcard": {
                                "iccid": "iccid-123",
                                "apn": "test.apn",
                                "signal": {"network_type": "5G"},
                            },
                        }
                    ]
                }
            },
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")
    client._firmware_version = (4, 7, 0, 0)

    info = await client.modem.get_modem_info()
    assert len(info) == 1
    assert info[0].bus == "1-1"
    assert info[0].model == "test-modem"
    assert info[0].iccid == "iccid-123"
    assert info[0].network_type == "5G"
    assert info[0].apn == "test.apn"


async def test_wireguard_state_uses_vpn_client_module_for_4_9() -> None:
    session = FakeSession([{"result": {"status_list": [{"type": "wireguard", "peer_id": 7}]}}])
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")
    client._firmware_version = (4, 9, 0, 0)

    assert await client.wg_client.get_wireguard_state() == [{"type": "wireguard", "peer_id": 7}]
    assert session.requests[0]["json"]["params"] == ["sid-1", "vpn-client", "get_status", {}]


async def test_wireguard_state_uses_legacy_module_for_4_8() -> None:
    session = FakeSession([{"result": {"status": 1, "peer_id": 7}}])
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")
    client._firmware_version = (4, 8, 0, 0)

    assert await client.wg_client.get_wireguard_state() == [{"status": 1, "peer_id": 7}]
    assert session.requests[0]["json"]["params"] == ["sid-1", "wg-client", "get_status", {}]


async def test_custom_call_sends_expected_payloads() -> None:
    session = FakeSession(
        [
            {"result": {"ok": True}},
            {"result": {"challenge": "123"}},
            {"result": {"result": 0}},
        ]
    )
    client = GLinetApiClient("http://router/rpc", session, sid="sid-1")

    assert await client.custom_call("system/get_info", {"arg": 1}) == {"ok": True}
    assert await client.custom_call("challenge", {"username": "root"}) == {"challenge": "123"}
    assert await client.custom_call("call", ["system", "reboot", {"delay": 0}]) == {"result": 0}

    assert [request["json"] for request in session.requests] == [
        {
            "method": "call",
            "jsonrpc": "2.0",
            "params": ["sid-1", "system", "get_info", {"arg": 1}],
            "id": 0,
        },
        {
            "method": "challenge",
            "jsonrpc": "2.0",
            "params": {"username": "root"},
            "id": 0,
        },
        {
            "method": "call",
            "jsonrpc": "2.0",
            "params": ["sid-1", "system", "reboot", {"delay": 0}],
            "id": 0,
        },
    ]


@pytest.mark.parametrize(
    ("verify_ssl", "expected_ssl"),
    [
        (True, None),
        (False, False),
    ],
)
async def test_send_request_forwards_verify_ssl_to_session(
    verify_ssl: bool, expected_ssl: bool | None
) -> None:
    session = FakeSession([{"jsonrpc": "2.0", "result": {"ok": True}, "id": 0}])
    client = GLinetApiClient("http://router/rpc", session, verify_ssl=verify_ssl)

    assert await client.is_router_reachable() is True

    assert len(session.requests) == 1
    assert session.requests[0]["ssl"] is expected_ssl


async def test_send_request_defaults_to_disabled_ssl_verification() -> None:
    session = FakeSession([{"jsonrpc": "2.0", "result": {"ok": True}, "id": 0}])
    client = GLinetApiClient("http://router/rpc", session)

    assert await client.is_router_reachable() is True

    assert session.requests[0]["ssl"] is False


async def test_context_manager_owns_and_closes_session() -> None:
    """When no session is supplied, the client creates one and closes it on exit."""
    client = GLinetApiClient("http://router/rpc")
    assert client._owns_session is True

    async with client as c:
        assert c is client
        assert c._session.closed is False

    assert client._session.closed is True


async def test_context_manager_does_not_close_caller_owned_session() -> None:
    """When a session is supplied, the caller retains ownership."""
    session = FakeSession([])
    client = GLinetApiClient("http://router/rpc", session)

    async with client:
        # FakeSession does not expose `.closed`, but close() must be a no-op
        # for caller-owned sessions. We verify via the internal flag.
        assert client._owns_session is False

    # Should not raise; the client does not close sessions it does not own.
    assert client._session is session


async def test_close_is_idempotent() -> None:
    client = GLinetApiClient("http://router/rpc")
    await client.close()
    # Second call must not raise even though the session is already closed.
    await client.close()


async def test_custom_call_rejects_non_dict_for_challenge() -> None:
    client = GLinetApiClient("http://router/rpc", FakeSession([]))
    with pytest.raises(TypeError, match="challenge"):
        await client.custom_call("challenge", ["not", "a", "dict"])


async def test_custom_call_rejects_non_dict_for_login() -> None:
    client = GLinetApiClient("http://router/rpc", FakeSession([]))
    with pytest.raises(TypeError, match="login"):
        await client.custom_call("login", [1, 2, 3])


async def test_custom_call_accepts_dict_for_challenge() -> None:
    session = FakeSession([{"jsonrpc": "2.0", "result": {"alg": 1}, "id": 0}])
    client = GLinetApiClient("http://router/rpc", session)
    result = await client.custom_call("challenge", {"username": "root"})
    assert result == {"alg": 1}
    assert session.requests[0]["json"]["params"] == {"username": "root"}


async def test_unsupported_cipher_algorithm_lists_supported() -> None:
    session = FakeSession(
        [
            # challenge response
            {
                "jsonrpc": "2.0",
                "result": {"alg": 9, "salt": "abc", "nonce": "xyz"},
                "id": 0,
            }
        ]
    )
    client = GLinetApiClient("http://router/rpc", session)
    with pytest.raises(ValueError, match="Unsupported router cipher algorithm 9"):
        await client.authenticate("root", "secret")


async def test_unsupported_digest_lists_supported() -> None:
    session = FakeSession(
        [
            # challenge response with an unsupported hash method
            {
                "jsonrpc": "2.0",
                "result": {
                    "alg": 1,
                    "salt": "abc",
                    "nonce": "xyz",
                    "hash-method": "blake2",
                },
                "id": 0,
            }
        ]
    )
    client = GLinetApiClient("http://router/rpc", session)
    with pytest.raises(ValueError, match="Unsupported router hash method"):
        await client.authenticate("root", "secret")


def test_client_error_is_re_exported() -> None:
    from aiohttp import ClientError as AiohttpClientError

    from glinet import ClientError

    assert ClientError is AiohttpClientError


async def test_custom_auth_hasher_can_be_registered() -> None:
    """A subclass or patched instance can register a new algorithm."""
    from passlib.hash import md5_crypt

    session = FakeSession(
        [
            # challenge with a previously-unsupported algorithm id
            {
                "jsonrpc": "2.0",
                "result": {
                    "alg": 1,
                    "salt": "ab",
                    "nonce": "cd",
                    "hash-method": "md5",
                },
                "id": 0,
            },
            # login response with a sid
            {"jsonrpc": "2.0", "result": {"sid": "abc123"}, "id": 0},
        ]
    )
    client = GLinetApiClient("http://router/rpc", session)
    # Override at instance level to simulate a firmware-specific extension.
    client.auth_hashers = {1: md5_crypt}
    await client.authenticate("root", "secret")
    assert client.sid == "abc123"
    assert client.logged_in is True


def test_constructor_with_no_session_marks_self_as_owner() -> None:
    client = GLinetApiClient("http://router/rpc")
    assert client._owns_session is True
    assert client._session is not None


def test_constructor_with_session_marks_caller_as_owner() -> None:
    session = FakeSession([])
    client = GLinetApiClient("http://router/rpc", session)
    assert client._owns_session is False
    assert client._session is session


async def test_authenticate_populates_default_hashers_lazily() -> None:
    """After calling authenticate, auth_hashers should hold the defaults."""
    session = FakeSession(
        [
            {
                "jsonrpc": "2.0",
                "result": {
                    "alg": 1,
                    "salt": "ab",
                    "nonce": "cd",
                    "hash-method": "md5",
                },
                "id": 0,
            },
            {"jsonrpc": "2.0", "result": {"sid": "abc123"}, "id": 0},
        ]
    )
    client = GLinetApiClient("http://router/rpc", session)
    assert client.auth_hashers == {}  # not populated yet
    await client.authenticate("root", "secret")
    assert set(client.auth_hashers) == {1, 5, 6}


async def test_authenticate_without_passlib_raises_helpful_error(monkeypatch) -> None:
    """If passlib is not importable, authenticate() explains how to install it."""
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):  # noqa: ANN001
        if name == "passlib" or name.startswith("passlib."):
            raise ImportError("simulated missing passlib")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    client = GLinetApiClient("http://router/rpc", FakeSession([]))
    with pytest.raises(ImportError, match=r"pip install 'glinet\[auth\]'"):
        await client.authenticate("root", "secret")
