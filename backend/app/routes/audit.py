from __future__ import annotations

from fastapi import Depends

from app.agent_executor import AgentCommandExecutor
from app.agent_moonraker import status_payload
from app.routes.auth import require_current_user_when_configured
from app.routes.support import *

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.get("/api/audit/read-only")
async def read_only_audit() -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printers = repository.list_printers()
    if not printers:
        raise HTTPException(status_code=404, detail="printer not found")
    printer = printers[0]
    try:
        job = await AgentCommandExecutor(settings.database_path).run(printer, job_type="remote_moonraker_status")
        printer_info, server_info, system_info, proc_stats, update_status = status_payload(job.result)
    except HTTPException as exc:
        return _build_unreachable_audit("agent", Exception(str(exc.detail)))

    audit = build_read_only_audit(
        printer_info=printer_info,
        server_info=server_info,
        update_status=update_status,
        system_info=system_info,
        proc_stats=proc_stats,
        source="agent",
    )
    return {
        "connected": True,
        "moonraker_url": "agent",
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

    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_moonraker_status",
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
        printer_info, server_info, system_info, proc_stats, update_status = status_payload(job.result)
    except HTTPException as exc:
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            payload = latest_snapshot.payload
            update_status = apply_update_alert_silences(
                _dict(payload.get("update_status")),
                get_update_alert_silence_repository(settings).list_for_printer(printer.id),
            )
            audit = build_read_only_audit(
                printer_info=_dict(payload.get("printer_info")),
                server_info=_dict(payload.get("server_info")),
                update_status=update_status,
                system_info=_dict(payload.get("system_info")),
                proc_stats=_dict(payload.get("proc_stats")),
                data_state="last_snapshot",
                source=f"snapshot:{latest_snapshot.id}",
                error=str(exc.detail),
            )
            return {
                "connected": False,
                "moonraker_url": "agent",
                **audit,
            }
        return _build_unreachable_audit("agent", Exception(str(exc.detail)))

    update_status = apply_update_alert_silences(
        update_status,
        get_update_alert_silence_repository(settings).list_for_printer(printer.id),
    )
    audit = build_read_only_audit(
        printer_info=printer_info,
        server_info=server_info,
        update_status=update_status,
        system_info=system_info,
        proc_stats=proc_stats,
        source="agent",
    )
    return {
        "connected": True,
        "moonraker_url": "agent",
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
