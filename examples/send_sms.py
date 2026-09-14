"""Send an SMS via the router's SIM card (if present).

Usage:
    python examples/send_sms.py \\
        --host http://192.168.8.1 \\
        --password secret \\
        --recipient +15551234567 \\
        --text "Hello from python-glinet-router"

Requires `glinet[auth]`.
"""

from __future__ import annotations

import argparse
import asyncio

from glinet_router import GLinetApiClient
from glinet_router.exceptions import APIClientError, NonZeroResponse


async def main() -> None:
    parser = argparse.ArgumentParser(description="Send an SMS via GL.iNet router.")
    parser.add_argument("--host", default="http://192.168.8.1")
    parser.add_argument("--username", default="root")
    parser.add_argument("--password", required=True)
    parser.add_argument("--recipient", required=True, help="E.164 phone number.")
    parser.add_argument("--text", required=True, help="SMS body.")
    args = parser.parse_args()

    async with GLinetApiClient(f"{args.host}/rpc") as client:
        await client.authenticate(args.username, args.password)
        try:
            info = await client.modem.get_info()
        except (APIClientError, NonZeroResponse) as exc:
            print(f"Modem not available: {exc}")
            return

        buses = [modem.bus for modem in info]
        if not buses:
            print("No modem found on this router.")
            return

        result = await client.modem.send_sms(
            bus=buses[0],
            recipient=args.recipient,
            text=args.text,
        )
        print(f"SMS send result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
