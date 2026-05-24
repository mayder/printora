from __future__ import annotations

from app.routes.support import *

router = APIRouter()


@router.get("/api/audit/read-only")
async def read_only_audit() -> dict[str, Any]:
    settings = get_settings()
    client = get_moonraker_client(settings)
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        return _build_unreachable_audit(settings.moonraker_url, exc)

    audit = build_read_only_audit(
        printer_info=printer_info,
        server_info=server_info,
        update_status=update_status,
        system_info=system_info,
        proc_stats=proc_stats,
        source=settings.moonraker_url,
    )
    return {
        "connected": True,
        "moonraker_url": settings.moonraker_url,
        **audit,
    }




@router.get("/api/printers/{printer_id}/audit/read-only")
async def printer_read_only_audit(printer_id: int) -> dict[str, Any]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            payload = latest_snapshot.payload
            audit = build_read_only_audit(
                printer_info=_dict(payload.get("printer_info")),
                server_info=_dict(payload.get("server_info")),
                update_status=_dict(payload.get("update_status")),
                system_info=_dict(payload.get("system_info")),
                proc_stats=_dict(payload.get("proc_stats")),
                data_state="last_snapshot",
                source=f"snapshot:{latest_snapshot.id}",
                error=str(exc),
            )
            return {
                "connected": False,
                "moonraker_url": printer.moonraker_url,
                **audit,
            }
        return _build_unreachable_audit(printer.moonraker_url, exc)

    audit = build_read_only_audit(
        printer_info=printer_info,
        server_info=server_info,
        update_status=update_status,
        system_info=system_info,
        proc_stats=proc_stats,
        source=printer.moonraker_url,
    )
    return {
        "connected": True,
        "moonraker_url": printer.moonraker_url,
        **audit,
    }




@router.get("/api/audit/host-read-only")
async def host_read_only_audit() -> dict[str, Any]:
    settings = get_settings()
    result = await collect_host_audit(
        mode=settings.host_audit_mode,
        ssh_target=settings.host_audit_ssh_target,
        timeout_seconds=settings.host_audit_timeout_seconds,
    )
    return {
        "safe_mode": "read_only",
        "connected": result.executed and result.exit_code == 0,
        "mode": result.mode,
        "executed": result.executed,
        "exit_code": result.exit_code,
        "summary": _host_summary(result.findings),
        "counts": _count_findings(result.findings),
        "findings": [finding.__dict__ for finding in result.findings],
        "section_summary": summarize_sections(result.sections),
    }
