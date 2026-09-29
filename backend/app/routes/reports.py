from __future__ import annotations

from fastapi import Depends

from app.agent_executor import AgentCommandExecutor
from app.agent_moonraker import runtime_status_payload, status_payload
from app.routes.auth import require_current_user_when_configured
from app.routes.support import *

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.get("/api/printers/{printer_id}/reports/sanitized")
async def sanitized_report(printer_id: int) -> SanitizedReport:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    backup_repository = get_backup_repository(settings)
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
        runtime_alerts, runtime_alerts_state = runtime_status_payload(job.result)
        snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=2)
        latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)
        update_status = apply_update_alert_silences(
            update_status,
            get_update_alert_silence_repository(settings).list_for_printer(printer.id),
        )
        health_payload = {
            "printer_id": printer.id,
            "moonraker_url": printer.moonraker_url,
            **build_printer_health(
                printer_info=printer_info,
                server_info=server_info,
                update_status=update_status,
                system_info=system_info,
                proc_stats=proc_stats,
                snapshots=snapshots,
                latest_diff=latest_diff,
                runtime_alerts=runtime_alerts,
                runtime_alerts_state=runtime_alerts_state,
                source="agent",
            ),
        }
    except HTTPException as exc:
        snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=2)
        latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            payload = latest_snapshot.payload
            update_status = apply_update_alert_silences(
                _dict(payload.get("update_status")),
                get_update_alert_silence_repository(settings).list_for_printer(printer.id),
            )
            health_payload = {
                "printer_id": printer.id,
                "moonraker_url": printer.moonraker_url,
                **build_printer_health(
                    printer_info=_dict(payload.get("printer_info")),
                    server_info=_dict(payload.get("server_info")),
                    update_status=update_status,
                    system_info=_dict(payload.get("system_info")),
                    proc_stats=_dict(payload.get("proc_stats")),
                    snapshots=snapshots,
                    latest_diff=latest_diff,
                    data_state="last_snapshot",
                    source=f"snapshot:{latest_snapshot.id}",
                    error=str(exc.detail),
                ),
            }
        else:
            health_payload = {
                "printer_id": printer.id,
                "moonraker_url": "agent",
                **build_unreachable_health("agent", str(exc.detail)),
            }

    backup_runs = backup_repository.list_runs(printer.id, limit=5)
    return build_sanitized_report(
        printer=printer,
        health=health_payload,
        snapshots=snapshots,
        latest_diff=latest_diff,
        backup_runs=backup_runs,
    )
