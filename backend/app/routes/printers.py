from __future__ import annotations

import time

from fastapi import Depends

from app.agent_executor import AgentCommandExecutor
from app.agent_moonraker import status_payload
from app.discovery import PrinterDiscoveryResponse
from app.routes.auth import require_current_user_when_configured
from app.routes.support import *

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.get("/api/moonraker/status")
async def moonraker_status() -> dict[str, Any]:
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
        printer_info, server_info, system_info, proc_stats, _update_status = status_payload(job.result)
    except HTTPException as exc:
        return {
            "connected": False,
            "moonraker_url": "agent",
            "error": str(exc.detail),
        }

    return {
        "connected": True,
        "moonraker_url": "agent",
        "printer": printer_info,
        "server": server_info,
        "system": system_info,
        "proc_stats": proc_stats,
    }




@router.get("/api/printers")
async def list_printers() -> dict[str, list[PrinterRecord]]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    return {"printers": repository.list_printers()}




@router.post("/api/printers")
async def create_printer(payload: PrinterCreate) -> PrinterRecord:
    settings = get_settings()
    repository = get_printer_repository(settings)
    try:
        return repository.create_printer(payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc



@router.get("/api/printers/discover")
async def discover_printers(cidr: str | None = None) -> PrinterDiscoveryResponse:
    return PrinterDiscoveryResponse(
        cidr=cidr or "",
        safe_mode="agent_required",
        scanned_hosts=0,
        candidates=[],
        warnings=["Descoberta direta pela API desativada para cloud. Use um agente pareado na rede para descoberta futura."],
    )




@router.post("/api/printers/test-connection")
async def test_printer_connection(payload: PrinterConnectionTestRequest) -> PrinterConnectionTestResponse:
    moonraker_url = str(payload.moonraker_url).rstrip("/")
    moonraker = ConnectionCheckResult(
        ok=False,
        target=moonraker_url,
        detail="Teste direto pela API desativado para cloud. Instale/pareie o agente e valide a impressora pela tela Agentes.",
    )
    ssh = ConnectionCheckResult(
        ok=False,
        target=f"{payload.ssh_host}:{payload.ssh_port}" if payload.ssh_host else "ssh",
        detail="Teste SSH direto pela API desativado para cloud.",
    ) if payload.ssh_host else None
    return PrinterConnectionTestResponse(
        safe_mode="read_only",
        moonraker=moonraker,
        ssh=ssh,
    )



@router.get("/api/printers/{printer_id}")
async def get_printer(printer_id: int) -> PrinterRecord:
    settings = get_settings()
    repository = get_printer_repository(settings)
    record = repository.get_printer(printer_id)
    if record is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return record




@router.put("/api/printers/{printer_id}")
async def update_printer(printer_id: int, payload: PrinterUpdate) -> PrinterRecord:
    settings = get_settings()
    repository = get_printer_repository(settings)
    try:
        record = repository.update_printer(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if record is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return record




@router.get("/api/printers/{printer_id}/moonraker/status")
async def printer_moonraker_status(printer_id: int) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_moonraker_status",
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
        printer_info, server_info, system_info, proc_stats, _update_status = status_payload(job.result)
    except HTTPException as exc:
        return {
            "connected": False,
            "printer_id": printer.id,
            "moonraker_url": "agent",
            "error": str(exc.detail),
        }

    return {
        "connected": True,
        "printer_id": printer.id,
        "moonraker_url": "agent",
        "printer": printer_info,
        "server": server_info,
        "system": system_info,
        "proc_stats": proc_stats,
    }




@router.get("/api/printers/{printer_id}/health")
async def printer_health(printer_id: int) -> dict[str, Any]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    snapshot_repository = get_snapshot_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    started_at = time.perf_counter()
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
            snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=2)
            latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)
            payload = latest_snapshot.payload
            update_status = apply_update_alert_silences(
                _dict(payload.get("update_status")),
                get_update_alert_silence_repository(settings).list_for_printer(printer.id),
            )
            return {
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
        return {
            "printer_id": printer.id,
            "moonraker_url": "agent",
            **build_unreachable_health("agent", str(exc.detail)),
        }
    api_latency_ms = (time.perf_counter() - started_at) * 1000

    snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=2)
    latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)
    update_status = apply_update_alert_silences(
        update_status,
        get_update_alert_silence_repository(settings).list_for_printer(printer.id),
    )

    return {
        "printer_id": printer.id,
        "moonraker_url": "agent",
        **build_printer_health(
            printer_info=printer_info,
            server_info=server_info,
            update_status=update_status,
            system_info=system_info,
            proc_stats=proc_stats,
            snapshots=snapshots,
            latest_diff=latest_diff,
            source="agent",
            api_latency_ms=api_latency_ms,
        ),
    }


@router.get("/api/printers/{printer_id}/network-diagnostics")
async def printer_network_diagnostics(printer_id: int) -> dict[str, Any]:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    ssh_access = repository.get_ssh_access(printer_id)
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_host_script",
            payload={
                "kind": "network_diagnostics",
                "script": _agent_network_diagnostics_script(printer.moonraker_url),
                "timeout_seconds": max(settings.request_timeout_seconds, settings.host_audit_timeout_seconds),
            },
            timeout_seconds=max(settings.request_timeout_seconds, settings.host_audit_timeout_seconds, 10.0),
        )
        result = job.result if isinstance(job.result, dict) else {}
        return {
            "safe_mode": "agent_read_only",
            "printer_id": printer.id,
            "moonraker_url": "agent",
            "host": printer.moonraker_url,
            "dns": {"ok": True, "duration_ms": None, "addresses": [], "error": None},
            "ping": {"ok": True, "source": "agent", "error": None},
            "configured_http": {"ok": True, "url": "agent-local", "status_code": None, "total_ms": None, "error": None},
            "direct_ip_http": None,
            "ssh": {"ok": True, "source": "agent-local", "detail": "Diagnóstico executado no host do agente."} if ssh_access else None,
            "recommendation": str(result.get("stdout") or "")[-1200:] or "Diagnóstico de rede executado pelo agente.",
        }
    except Exception as exc:
        return {
            "safe_mode": "read_only",
            "printer_id": printer.id,
            "moonraker_url": printer.moonraker_url,
            "host": printer.moonraker_url,
            "dns": {"ok": False, "duration_ms": None, "addresses": [], "error": str(exc)},
            "ping": {"ok": False, "error": "diagnostico nao concluido"},
            "configured_http": {"ok": False, "url": printer.moonraker_url, "status_code": None, "total_ms": None, "error": str(exc)},
            "direct_ip_http": None,
            "ssh": None,
            "recommendation": "Diagnostico de rede nao concluiu. Tente novamente; a falha nao bloqueia o restante do Printora.",
        }


def _agent_network_diagnostics_script(moonraker_url: str) -> str:
    return f"""set +e
printf 'agent_host='; hostname 2>/dev/null || true
printf 'moonraker_local='
curl -fsS --max-time 5 http://127.0.0.1:7125/server/info >/dev/null && printf 'ok\\n' || printf 'erro\\n'
printf 'moonraker_configured='
curl -fsS --max-time 5 {moonraker_url!r}/server/info >/dev/null && printf 'ok\\n' || printf 'erro\\n'
printf 'ip='
hostname -I 2>/dev/null || true
"""




@router.get("/api/printers/{printer_id}/updates/status")
async def printer_update_status(printer_id: int) -> UpdateStatusResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_update_status",
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
        update_status = status_payload(job.result)[4]
    except HTTPException:
        return build_update_status({})
    update_status = apply_update_alert_silences(
        update_status,
        get_update_alert_silence_repository(settings).list_for_printer(printer_id),
    )
    return build_update_status(update_status)
