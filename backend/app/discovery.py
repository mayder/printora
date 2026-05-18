import asyncio
import ipaddress
import socket
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import BaseModel, ConfigDict

from app.printers import PrinterRecord


MOONRAKER_PORT = 7125
MAX_DISCOVERY_HOSTS = 256


class DiscoveredPrinter(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    moonraker_url: str
    address: str
    klippy_connected: bool | None
    klippy_state: str | None
    moonraker_version: str | None
    already_registered: bool


class PrinterDiscoveryResponse(BaseModel):
    cidr: str
    safe_mode: str
    scanned_hosts: int
    candidates: list[DiscoveredPrinter]
    warnings: list[str]


@dataclass(frozen=True)
class DiscoveryTarget:
    address: str
    url: str


async def discover_moonraker_printers(
    *,
    cidr: str | None,
    registered_printers: list[PrinterRecord],
    timeout_seconds: float = 0.35,
) -> PrinterDiscoveryResponse:
    network, warnings = _resolve_discovery_network(cidr)
    registered_urls = {printer.moonraker_url.rstrip("/") for printer in registered_printers}
    targets = [DiscoveryTarget(address=str(host), url=f"http://{host}:{MOONRAKER_PORT}") for host in network.hosts()]

    timeout = httpx.Timeout(timeout_seconds, connect=timeout_seconds)
    limits = httpx.Limits(max_connections=64, max_keepalive_connections=0)
    async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
        results = await asyncio.gather(*[_probe_target(client, target, registered_urls) for target in targets])

    candidates = sorted((result for result in results if result is not None), key=lambda item: item.address)
    return PrinterDiscoveryResponse(
        cidr=str(network),
        safe_mode="read_only_http_get_server_info",
        scanned_hosts=len(targets),
        candidates=candidates,
        warnings=warnings,
    )


def _resolve_discovery_network(cidr: str | None) -> tuple[ipaddress.IPv4Network, list[str]]:
    warnings: list[str] = []
    if cidr:
        network = ipaddress.ip_network(cidr, strict=False)
        if not isinstance(network, ipaddress.IPv4Network):
            raise ValueError("only IPv4 networks are supported")
    else:
        local_ip = _detect_local_ipv4()
        network = ipaddress.ip_network(f"{local_ip}/24", strict=False)
        warnings.append("CIDR detectado automaticamente a partir do IP local.")

    if not (network.is_private or network.is_loopback or network.is_link_local):
        raise ValueError("discovery is limited to private, loopback, or link-local networks")
    if network.num_addresses > MAX_DISCOVERY_HOSTS:
        raise ValueError("discovery is limited to /24 or smaller networks")
    return network, warnings


def _detect_local_ipv4() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.settimeout(0.2)
        try:
            sock.connect(("8.8.8.8", 80))
            address = sock.getsockname()[0]
        except OSError:
            address = "127.0.0.1"
    return address


async def _probe_target(
    client: httpx.AsyncClient,
    target: DiscoveryTarget,
    registered_urls: set[str],
) -> DiscoveredPrinter | None:
    try:
        response = await client.get(f"{target.url}/server/info")
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError):
        return None

    result = payload.get("result") if isinstance(payload, dict) else None
    if not isinstance(result, dict) or "moonraker_version" not in result:
        return None

    name = _name_from_server_info(result, target.address)
    return DiscoveredPrinter(
        name=name,
        moonraker_url=target.url,
        address=target.address,
        klippy_connected=_optional_bool(result.get("klippy_connected")),
        klippy_state=_optional_string(result.get("klippy_state")),
        moonraker_version=_optional_string(result.get("moonraker_version")),
        already_registered=target.url.rstrip("/") in registered_urls,
    )


def _name_from_server_info(server_info: dict[str, Any], address: str) -> str:
    hostname = server_info.get("hostname")
    if isinstance(hostname, str) and hostname.strip():
        return hostname.strip()
    return f"Moonraker {address}"


def _optional_string(value: Any) -> str | None:
    return value if isinstance(value, str) else None


def _optional_bool(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None
