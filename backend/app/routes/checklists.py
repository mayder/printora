from __future__ import annotations

from app.routes.support import *

router = APIRouter()


@router.get("/api/checklist/post-update")
async def post_update_checklist() -> dict[str, Any]:
    settings = get_settings()
    client = get_moonraker_client(settings)
    try:
        printer_info = await client.printer_info()
        server_info = await client.server_info()
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        return build_unavailable_post_update_checklist(
            data_state="offline",
            source=settings.moonraker_url,
            error=str(exc),
        )
    return build_post_update_checklist(
        printer_info,
        server_info,
        update_status,
        source=settings.moonraker_url,
    )




@router.get("/api/printers/{printer_id}/checklist/post-update")
async def printer_post_update_checklist(printer_id: int) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        printer_info = await client.printer_info()
        server_info = await client.server_info()
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            payload = latest_snapshot.payload
            update_status = apply_update_alert_silences(
                _dict(payload.get("update_status")),
                get_update_alert_silence_repository(settings).list_for_printer(printer.id),
            )
            return build_post_update_checklist(
                _dict(payload.get("printer_info")),
                _dict(payload.get("server_info")),
                update_status,
                data_state="last_snapshot",
                source=f"snapshot:{latest_snapshot.id}",
                error=str(exc),
            )
        return build_unavailable_post_update_checklist(
            data_state="offline",
            source=printer.moonraker_url,
            error=str(exc),
        )
    update_status = apply_update_alert_silences(
        update_status,
        get_update_alert_silence_repository(settings).list_for_printer(printer.id),
    )
    return build_post_update_checklist(
        printer_info,
        server_info,
        update_status,
        source=printer.moonraker_url,
    )
