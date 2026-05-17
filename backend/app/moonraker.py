from typing import Any

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

    async def printer_info(self) -> dict[str, Any]:
        return await self.get_json("/printer/info")

    async def server_info(self) -> dict[str, Any]:
        return await self.get_json("/server/info")

    async def update_status(self) -> dict[str, Any]:
        return await self.get_json("/machine/update/status")

    async def system_info(self) -> dict[str, Any]:
        return await self.get_json("/machine/system_info")

    async def proc_stats(self) -> dict[str, Any]:
        return await self.get_json("/machine/proc_stats")
