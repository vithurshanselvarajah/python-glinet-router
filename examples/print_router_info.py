"""Print basic router info.

Usage:
    python examples/print_router_info.py --host http://192.168.8.1 --password secret

Requires `glinet[auth]`:
    pip install 'glinet[auth]'
"""

from __future__ import annotations

import argparse
import asyncio

from glinet import GLinetApiClient


async def main() -> None:
    parser = argparse.ArgumentParser(description="Print GL.iNet router info.")
    parser.add_argument("--host", default="http://192.168.8.1", help="Router URL.")
    parser.add_argument("--username", default="root", help="Router admin username.")
    parser.add_argument("--password", required=True, help="Router admin password.")
    parser.add_argument(
        "--verify-ssl",
        action="store_true",
        help="Verify the router's TLS certificate (off by default).",
    )
    args = parser.parse_args()

    async with GLinetApiClient(
        f"{args.host}/rpc", verify_ssl=args.verify_ssl
    ) as client:
        await client.authenticate(args.username, args.password)

        info = await client.system.get_info()
        print("Router info")
        print(f"  model           : {info.model}")
        print(f"  firmware version: {info.firmware_version}")
        print(f"  mac             : {info.mac}")
        print(f"  serial number   : {info.sn}")
        print(f"  device id       : {info.device_id}")

        status = await client.system.get_status()
        print("\nSystem status")
        print(f"  uptime          : {status.uptime} s")
        print(f"  load average    : {status.load_average}")
        print(f"  memory used     : {status.memory_total - status.memory_free} bytes")
        print(f"  flash used      : {status.flash_total - status.flash_free} bytes")
        print(f"  temperature     : {status.temperature} \u00b0C")

        clients = await client.clients.get_online()
        print(f"\n{len(clients)} client(s) online")


if __name__ == "__main__":
    asyncio.run(main())
