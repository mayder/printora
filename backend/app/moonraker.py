from typing import Any
from urllib.parse import quote

import httpx


class MoonrakerClient:
    def __init__(self, base_url: str, timeout_seconds: float = 5.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds

    async def get_json(self, path: str) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url)
            response.raise_for_status()
            payload = response.json()
        result = payload.get("result")
        return result if isinstance(result, dict) else payload

    async def post_json(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(url, json=payload) if payload is not None else await client.post(url)
            response.raise_for_status()
            response_payload = response.json()
        result = response_payload.get("result")
        return result if isinstance(result, dict) else response_payload

    async def printer_info(self) -> dict[str, Any]:
        return await self.get_json("/printer/info")

    async def server_info(self) -> dict[str, Any]:
        return await self.get_json("/server/info")

    async def update_status(self) -> dict[str, Any]:
        return await self.get_json("/machine/update/status")

    async def refresh_update_status(self, name: str | None = None) -> dict[str, Any]:
        path = f"/machine/update/refresh?name={quote(name)}" if name else "/machine/update/refresh"
        return await self.post_json(path)

    async def update_all(self) -> dict[str, Any]:
        return await self.post_json("/machine/update/full")

    async def update_system(self) -> dict[str, Any]:
        return await self.post_json("/machine/update/system")

    async def update_core_component(self, name: str) -> dict[str, Any]:
        return await self.post_json(f"/machine/update/{name}")

    async def update_client(self, name: str) -> dict[str, Any]:
        return await self.post_json(f"/machine/update/client?name={quote(name)}")

    async def system_info(self) -> dict[str, Any]:
        return await self.get_json("/machine/system_info")

    async def proc_stats(self) -> dict[str, Any]:
        return await self.get_json("/machine/proc_stats")
