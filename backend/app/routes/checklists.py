from __future__ import annotations

from fastapi import Depends

from app.agent_executor import AgentCommandExecutor
from app.agent_moonraker import status_payload
from app.routes.auth import require_current_user_when_configured
from app.routes.support import *

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.get("/api/checklist/post-update")
async def post_update_checklist() -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printers = repository.list_printers()
    if not printers:
        raise HTTPException(status_code=404, detail="printer not found")
    printer = printers[0]
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_moonraker_status",
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
        printer_info, server_info, _system_info, _proc_stats, update_status = status_payload(job.result)
    except HTTPException as exc:
        return build_unavailable_post_update_checklist(
            data_state="offline",
            source="agent",
            error=str(exc.detail),
        )
    return build_post_update_checklist(
        printer_info,
        server_info,
        update_status,
        source="agent",
    )




@router.get("/api/printers/{printer_id}/checklist/post-update")
async def printer_post_update_checklist(printer_id: int) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_moonraker_status",
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
        printer_info, server_info, _system_info, _proc_stats, update_status = status_payload(job.result)
    except HTTPException as exc:
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
                error=str(exc.detail),
            )
        return build_unavailable_post_update_checklist(
            data_state="offline",
            source="agent",
            error=str(exc.detail),
        )
    update_status = apply_update_alert_silences(
        update_status,
        get_update_alert_silence_repository(settings).list_for_printer(printer.id),
    )
    return build_post_update_checklist(
        printer_info,
        server_info,
        update_status,
        source="agent",
    )
