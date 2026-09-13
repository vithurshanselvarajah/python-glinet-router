"""Console entry point for `glinet`.

Install with `pip install 'glinet[cli]'` (pulls in `click`) and run:

    glinet info --host http://192.168.8.1 --password secret
    glinet call system/get_status --host http://router/rpc
    glinet call system reboot 0 --params '{}'
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

import click

from . import GLinetApiClient
from .exceptions import APIClientError


def _host(value: str) -> str:
    if not value.startswith(("http://", "https://")):
        raise click.BadParameter("must start with http:// or https://")
    return value.rstrip("/")


@click.group()
@click.version_option(package_name="glinet")
def main() -> None:
    """Command-line interface for the GL.iNet router JSON-RPC API."""


@main.command()
@click.option(
    "--host",
    default="http://192.168.8.1",
    callback=lambda _ctx, _param, value: _host(value),
    help="Router URL (default: %(default)s).",
)
@click.option("--username", default="root", help="Router admin username.")
@click.option(
    "--password",
    envvar="GLINET_PASSWORD",
    prompt=True,
    hide_input=True,
    help="Router admin password (or set GLINET_PASSWORD).",
)
@click.option(
    "--verify-ssl/--no-verify-ssl",
    default=False,
    help="Verify the router's TLS certificate.",
)
def info(host: str, username: str, password: str, verify_ssl: bool) -> None:
    """Print router info, status, and the list of online clients."""
    asyncio.run(_info(host, username, password, verify_ssl))


async def _info(
    host: str, username: str, password: str, verify_ssl: bool
) -> None:
    async with GLinetApiClient(f"{host}/rpc", verify_ssl=verify_ssl) as client:
        await client.authenticate(username, password)
        info_obj = await client.system.get_info()
        status = await client.system.get_status()
        clients = await client.clients.get_online()

        click.echo("Router info")
        click.echo(f"  model           : {info_obj.model}")
        click.echo(f"  firmware version: {info_obj.firmware_version}")
        click.echo(f"  mac             : {info_obj.mac}")
        click.echo(f"  serial number   : {info_obj.sn}")
        click.echo(f"  device id       : {info_obj.device_id}")
        click.echo("")
        click.echo("System status")
        click.echo(f"  uptime          : {status.uptime} s")
        click.echo(f"  load average    : {status.load_average}")
        click.echo(f"  temperature     : {status.temperature} \u00b0C")
        click.echo("")
        click.echo(f"{len(clients)} client(s) online")


@main.command()
@click.argument("method")
@click.option(
    "--host",
    default="http://192.168.8.1",
    callback=lambda _ctx, _param, value: _host(value),
    help="Router URL (default: %(default)s).",
)
@click.option("--username", default="root", help="Router admin username.")
@click.option(
    "--password",
    envvar="GLINET_PASSWORD",
    help=(
        "Router admin password (or set GLINET_PASSWORD). "
        "Omit for an unauthenticated call."
    ),
)
@click.option("--sid", help="Existing session id (skips authentication).")
@click.option(
    "--params",
    default="{}",
    help="JSON-encoded params (dict or list).",
)
@click.option(
    "--verify-ssl/--no-verify-ssl",
    default=False,
    help="Verify the router's TLS certificate.",
)
def call(
    method: str,
    host: str,
    username: str,
    password: str | None,
    sid: str | None,
    params: str,
    verify_ssl: bool,
) -> None:
    """Make a raw JSON-RPC call.

    METHOD may be a slash-separated module/method pair (e.g. "system/get_info")
    or a free-form name. For `challenge`/`login` you must pass a JSON object
    via `--params`.
    """
    asyncio.run(_call(method, host, username, password, sid, params, verify_ssl))


async def _call(
    method: str,
    host: str,
    username: str,
    password: str | None,
    sid: str | None,
    params: str,
    verify_ssl: bool,
) -> None:
    try:
        parsed: Any = json.loads(params)
    except json.JSONDecodeError as exc:
        raise click.BadParameter(f"invalid JSON: {exc}") from exc

    async with GLinetApiClient(
        f"{host}/rpc", verify_ssl=verify_ssl, sid=sid
    ) as client:
        if password and not sid:
            await client.authenticate(username, password)
        try:
            result = await client.custom_call(method, parsed)
        except APIClientError as exc:
            click.echo(f"error: {exc}", err=True)
            sys.exit(1)
        click.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
