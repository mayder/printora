import socket
import time
from typing import Any
from urllib.parse import urlparse, urlunparse
from urllib.parse import quote, urlencode

import httpx


_LOCAL_DNS_CACHE_TTL_SECONDS = 600
_local_dns_cache: dict[str, tuple[str, float]] = {}


class MoonrakerClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def get_json(self, path: str) -> dict[str, Any]:
        url, headers = _build_fast_local_url(self.base_url, path)
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            try:
                response = await client.get(url, headers=headers)
            except httpx.HTTPError:
                if headers:
                    _forget_cached_local_address(self.base_url)
                    response = await client.get(f"{self.base_url}/{path.lstrip('/')}")
                else:
                    raise
            response.raise_for_status()
            payload = response.json()
        result = payload.get("result")
        return result if isinstance(result, dict) else payload

    async def post_json(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        url, headers = _build_fast_local_url(self.base_url, path)
        async with httpx.AsyncClient(timeout=timeout_seconds or self.timeout_seconds) as client:
            try:
                response = await client.post(url, json=payload, headers=headers) if payload is not None else await client.post(url, headers=headers)
            except httpx.HTTPError:
                if headers:
                    _forget_cached_local_address(self.base_url)
                    original_url = f"{self.base_url}/{path.lstrip('/')}"
                    response = await client.post(original_url, json=payload) if payload is not None else await client.post(original_url)
                else:
                    raise
            response.raise_for_status()
            response_payload = response.json()
        result = response_payload.get("result")
        return result if isinstance(result, dict) else response_payload

    async def printer_info(self) -> dict[str, Any]:
        return await self.get_json("/printer/info")

    async def gcode_script(self, script: str, *, timeout_seconds: float | None = None) -> dict[str, Any]:
        return await self.post_json("/printer/gcode/script", {"script": script}, timeout_seconds=timeout_seconds)

    async def gcode_store(self, count: int = 20) -> dict[str, Any]:
        return await self.get_json(f"/server/gcode_store?count={count}")

    async def server_info(self) -> dict[str, Any]:
        return await self.get_json("/server/info")

    async def update_status(self) -> dict[str, Any]:
        return await self.get_json("/machine/update/status")

    async def refresh_update_status(self, name: str | None = None, *, timeout_seconds: float | None = None) -> dict[str, Any]:
        path = f"/machine/update/refresh?name={quote(name)}" if name else "/machine/update/refresh"
        return await self.post_json(path, timeout_seconds=timeout_seconds)

    async def update_all(self) -> dict[str, Any]:
        return await self.post_json("/machine/update/full")

    async def update_system(self) -> dict[str, Any]:
        return await self.post_json("/machine/update/system")

    async def update_core_component(self, name: str) -> dict[str, Any]:
        return await self.post_json(f"/machine/update/{name}")

    async def update_client(self, name: str) -> dict[str, Any]:
        return await self.post_json(f"/machine/update/client?name={quote(name)}")

    async def rollback_update(self, name: str) -> dict[str, Any]:
        return await self.post_json("/machine/update/rollback", {"name": name})

    async def system_info(self) -> dict[str, Any]:
        return await self.get_json("/machine/system_info")

    async def history_totals(self) -> dict[str, Any]:
        return await self.get_json("/server/history/totals")

    async def proc_stats(self) -> dict[str, Any]:
        return await self.get_json("/machine/proc_stats")

    async def printer_objects_list(self) -> list[str]:
        payload = await self.get_json("/printer/objects/list")
        objects = payload.get("objects", [])
        return [str(name) for name in objects] if isinstance(objects, list) else []

    async def printer_objects(self, objects: dict[str, list[str]]) -> dict[str, Any]:
        query = urlencode({name: ",".join(fields) for name, fields in objects.items()})
        return await self.get_json(f"/printer/objects/query?{query}")


def _build_fast_local_url(base_url: str, path: str) -> tuple[str, dict[str, str] | None]:
    clean_path = path.lstrip("/")
    parsed = urlparse(base_url)
    host = parsed.hostname or ""
    if parsed.scheme != "http" or not host.endswith(".local"):
        return f"{base_url.rstrip('/')}/{clean_path}", None
    address = _cached_local_address(host)
    if address is None:
        return f"{base_url.rstrip('/')}/{clean_path}", None
    netloc = f"{address}:{parsed.port}" if parsed.port else address
    url = urlunparse(parsed._replace(netloc=netloc, path=f"/{clean_path}", params="", query="", fragment=""))
    return url, {"Host": parsed.netloc}


def _cached_local_address(host: str) -> str | None:
    cached = _local_dns_cache.get(host)
    now = time.monotonic()
    if cached and cached[1] > now:
        return cached[0]
    try:
        records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
    except OSError:
        return None
    addresses = []
    for record in records:
        address = record[4][0]
        if address not in addresses:
            addresses.append(address)
    address = next((item for item in addresses if ":" not in item), None)
    if address is None:
        return None
    _local_dns_cache[host] = (address, now + _LOCAL_DNS_CACHE_TTL_SECONDS)
    return address


def _forget_cached_local_address(base_url: str) -> None:
    host = urlparse(base_url).hostname
    if host:
        _local_dns_cache.pop(host, None)
