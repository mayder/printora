from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MoonrakerGateway(Protocol):
    async def get_json(self, path: str) -> dict[str, Any]: ...

    async def post_json(
        self,
        path: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]: ...

    async def printer_info(self) -> dict[str, Any]: ...

    async def gcode_script(
        self,
        script: str,
        *,
        timeout_seconds: float | None = None,
    ) -> dict[str, Any]: ...

    async def printer_objects(self, objects: dict[str, list[str]]) -> dict[str, Any]: ...
