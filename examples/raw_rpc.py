"""Make an arbitrary JSON-RPC call without authenticating.

Use this for read-only endpoints (or when you already have a session id)
without paying the cost of `passlib` + the auth round-trip.

Usage:
    python examples/raw_rpc.py \\
        --host http://192.168.8.1 \\
        --method system/get_info
"""

from __future__ import annotations

import argparse
import asyncio
import json

from glinet_router import GLinetApiClient


async def main() -> None:
    parser = argparse.ArgumentParser(description="Make a raw GL.iNet JSON-RPC call.")
    parser.add_argument("--host", default="http://192.168.8.1")
    parser.add_argument("--sid", help="Existing session id (skips authentication).")
    parser.add_argument(
        "--method",
        required=True,
        help="Method to call, e.g. 'system/get_info' or 'system reboot 0'.",
    )
    parser.add_argument(
        "--params",
        default="{}",
        help="JSON-encoded params (dict or list).",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="HTTP timeout in seconds.",
    )
    args = parser.parse_args()

    params = json.loads(args.params)

    async with GLinetApiClient(f"{args.host}/rpc", sid=args.sid) as client:
        result = await client.custom_call(args.method, params)
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
