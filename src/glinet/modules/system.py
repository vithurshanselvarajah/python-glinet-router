from __future__ import annotations

from typing import Any

from glinet.const import LONG_TIMEOUT
from glinet.models import RouterStatus, SystemInfo
from glinet.utils import decode_firmware_version

from .base import BaseModule


class SystemModule(BaseModule):
    async def get_info(self) -> SystemInfo:
        response = await self._call("system", "get_info", timeout_seconds=LONG_TIMEOUT)
        info = dict(response)
        firmware_version = info.get("firmware_version", "")
        if firmware_version:
            self._client._firmware_version = decode_firmware_version(str(firmware_version))
        return SystemInfo(
            model=info.get("model", ""),
            firmware_version=str(firmware_version),
            mac=info.get("mac", ""),
            sn=info.get("sn", ""),
            device_id=info.get("device_id", ""),
        )

    async def get_status(self) -> RouterStatus:
        response = await self._call("system", "get_status", timeout_seconds=LONG_TIMEOUT)
        data = dict(response)
        return RouterStatus(
            uptime=int(data.get("uptime", 0) or 0),
            load_average=[float(value) for value in data.get("load_average", []) or []],
            memory_total=int(data.get("memory", {}).get("total", 0) or 0),
            memory_free=int(data.get("memory", {}).get("free", 0) or 0),
            memory_shared=int(data.get("memory", {}).get("shared", 0) or 0),
            memory_buffered=int(data.get("memory", {}).get("buffered", 0) or 0),
            temperature=(
                int(data["temperature"])
                if isinstance(data.get("temperature"), (int, float))
                else None
            ),
            flash_total=int(data.get("flash", {}).get("total", 0) or 0),
            flash_free=int(data.get("flash", {}).get("free", 0) or 0),
            network=list(data.get("network", []) or []),
            mcu=dict(data.get("mcu", {}) or {}),
        )

    async def reboot(self, delay: int = 0) -> dict[str, Any]:
        response = await self._call("system", "reboot", {"delay": delay})
        return dict(response) if response else {}

    async def get_kmwan_status(self) -> dict[str, Any]:
        try:
            response = await self._call("edgerouter", "get_kmwan_status")
        except Exception:
            return {}
        return dict(response) if response else {}
