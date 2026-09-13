from __future__ import annotations

from glinet.models import (
    ModemInfo,
    RouterStatus,
    SystemInfo,
    TailscaleConnection,
    WifiInterfaceInfo,
)


def test_tailscale_connection_values() -> None:
    assert TailscaleConnection.DISCONNECTED.value == 0
    assert TailscaleConnection.LOGIN_REQUIRED.value == 1
    assert TailscaleConnection.AUTHORIZATION_REQUIRED.value == 2
    assert TailscaleConnection.CONNECTED.value == 3
    assert TailscaleConnection.CONNECTING.value == 4


def test_system_info_defaults() -> None:
    info = SystemInfo()
    assert info.model == ""
    assert info.firmware_version == ""
    assert info.mac == ""
    assert info.sn == ""
    assert info.device_id == ""


def test_router_status_defaults() -> None:
    status = RouterStatus()
    assert status.uptime == 0
    assert status.load_average == []
    assert status.memory_total == 0
    assert status.memory_free == 0
    assert status.memory_shared == 0
    assert status.memory_buffered == 0
    assert status.temperature is None
    assert status.flash_total == 0
    assert status.flash_free == 0
    assert status.network == []
    assert status.mcu == {}


def test_wifi_interface_info_defaults() -> None:
    info = WifiInterfaceInfo()
    assert info.enabled is False
    assert info.ssid == ""
    assert info.guest is False
    assert info.hidden is False
    assert info.encryption == ""


def test_modem_info_defaults() -> None:
    info = ModemInfo()
    assert info.bus == ""
    assert info.model == ""
    assert info.imei == ""
    assert info.iccid == ""
    assert info.status == ""
    assert info.signal is None
    assert info.network_type == ""
    assert info.apn == ""
