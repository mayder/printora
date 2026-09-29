from __future__ import annotations

from fastapi import Depends

from app.routes.auth import require_current_user_when_configured
from app.routes.support import *

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.get("/api/printers/{printer_id}/plugins/audit")
async def plugin_audit(printer_id: int) -> PluginAuditResponse:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    snapshots = snapshot_repository.list_snapshots(printer_id, limit=20)
    latest_moonraker_snapshot = next((snapshot for snapshot in snapshots if snapshot.snapshot_type == "moonraker_status"), None)
    latest_snapshot = snapshot_repository.get_snapshot(latest_moonraker_snapshot.id) if latest_moonraker_snapshot else None
    return build_plugin_audit(printer_id, latest_snapshot)
