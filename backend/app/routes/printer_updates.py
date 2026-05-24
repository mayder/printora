from __future__ import annotations

from app.routes.support import *

router = APIRouter()


@router.post("/api/printers/{printer_id}/updates/refresh")
async def refresh_printer_update_status(
    printer_id: int,
    payload: UpdateRefreshRequest,
) -> UpdateActionResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    asyncio.create_task(_refresh_update_status_background(client, payload.name, max(settings.request_timeout_seconds, 30.0)))
    return UpdateActionResponse(
        safe_mode="moonraker_update_manager",
        action="refresh",
        target=payload.name or "all",
        accepted=True,
        message="Reanalise solicitada ao Moonraker. O status sera atualizado em segundo plano.",
        result={"scheduled": True},
    )


async def _refresh_update_status_background(client: MoonrakerClient, name: str | None, timeout_seconds: float) -> None:
    try:
        await client.refresh_update_status(name, timeout_seconds=timeout_seconds)
    except httpx.HTTPError:
        return




@router.post("/api/printers/{printer_id}/updates/run")
async def run_printer_update(printer_id: int, payload: UpdateRunRequest) -> UpdateActionResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    route, target = update_route_for_target(payload.target)
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        if target == "all":
            result = await client.update_all()
        elif target == "system":
            result = await client.update_system()
        elif target in {"klipper", "moonraker"}:
            result = await client.update_core_component(target)
        else:
            result = await client.update_client(target)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=_http_error_detail(exc)) from exc
    return UpdateActionResponse(
        safe_mode="moonraker_update_manager",
        action="update",
        target=target,
        accepted=True,
        message=f"Update solicitado ao Moonraker via {route}.",
        result=result,
    )
