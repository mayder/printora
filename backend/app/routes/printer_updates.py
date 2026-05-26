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
    await _guard_risky_update(client, target, payload.confirmation_phrase)
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


@router.post("/api/printers/{printer_id}/updates/rollback")
async def rollback_printer_update(printer_id: int, payload: PrinterUpdateRollbackRequest) -> UpdateActionResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    target = payload.target.strip()
    if target == "all":
        raise HTTPException(status_code=400, detail="rollback deve ser executado por componente")
    if payload.confirmation_phrase.strip() != ROLLBACK_CONFIRMATION_PHRASE:
        raise HTTPException(status_code=409, detail=f"rollback exige confirmação literal: {ROLLBACK_CONFIRMATION_PHRASE}")

    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        result = await client.rollback_update(target)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=_http_error_detail(exc)) from exc
    return UpdateActionResponse(
        safe_mode="moonraker_update_manager",
        action="rollback",
        target=target,
        accepted=True,
        message=f"Rollback de {target} solicitado ao Moonraker.",
        result=result,
    )


async def _guard_risky_update(client: MoonrakerClient, target: str, confirmation_phrase: str | None) -> None:
    try:
        status = build_update_status(await client.update_status())
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=_http_error_detail(exc)) from exc
    risky_components = risky_update_components(status, target)
    if not risky_components:
        return
    if (confirmation_phrase or "").strip() == RISK_UPDATE_CONFIRMATION_PHRASE:
        return
    component_names = ", ".join(item.title for item in risky_components)
    raise HTTPException(
        status_code=409,
        detail=(
            f"Update de risco alto bloqueado para {component_names}. "
            f"Para continuar, confirme literalmente: {RISK_UPDATE_CONFIRMATION_PHRASE}"
        ),
    )
