from __future__ import annotations

from app.routes.support import *

router = APIRouter()


@router.get("/api/moonraker/status")
async def moonraker_status() -> dict[str, Any]:
    settings = get_settings()
    client = get_moonraker_client(settings)
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
    except httpx.HTTPError as exc:
        return {
            "connected": False,
            "moonraker_url": settings.moonraker_url,
            "error": str(exc),
        }

    return {
        "connected": True,
        "moonraker_url": settings.moonraker_url,
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
    settings = get_settings()
    repository = get_printer_repository(settings)
    try:
        return await discover_moonraker_printers(
            cidr=cidr,
            registered_printers=repository.list_printers(),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/printers/test-connection")
async def test_printer_connection(payload: PrinterConnectionTestRequest) -> PrinterConnectionTestResponse:
    settings = get_settings()
    moonraker_url = str(payload.moonraker_url).rstrip("/")
    moonraker = await _test_moonraker_connection(moonraker_url, settings.request_timeout_seconds)
    ssh = None
    if payload.ssh_host:
        ssh_host = payload.ssh_host.strip()
        if ssh_host:
            ssh = await _test_tcp_connection(ssh_host, payload.ssh_port, settings.request_timeout_seconds)
    return PrinterConnectionTestResponse(
        safe_mode="read_only",
        moonraker=moonraker,
        ssh=ssh,
    )




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

    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
    except httpx.HTTPError as exc:
        return {
            "connected": False,
            "printer_id": printer.id,
            "moonraker_url": printer.moonraker_url,
            "error": str(exc),
        }

    return {
        "connected": True,
        "printer_id": printer.id,
        "moonraker_url": printer.moonraker_url,
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

    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    started_at = time.perf_counter()
    try:
        collected_status, update_status = await asyncio.gather(
            _collect_status(client),
            client.update_status(),
        )
        printer_info, server_info, system_info, proc_stats = collected_status
    except httpx.HTTPError as exc:
        latest_snapshot = _latest_moonraker_snapshot(snapshot_repository, printer.id)
        if latest_snapshot is not None:
            snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=2)
            latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)
            payload = latest_snapshot.payload
            return {
                "printer_id": printer.id,
                "moonraker_url": printer.moonraker_url,
                **build_printer_health(
                    printer_info=_dict(payload.get("printer_info")),
                    server_info=_dict(payload.get("server_info")),
                    update_status=_dict(payload.get("update_status")),
                    system_info=_dict(payload.get("system_info")),
                    proc_stats=_dict(payload.get("proc_stats")),
                    snapshots=snapshots,
                    latest_diff=latest_diff,
                    data_state="last_snapshot",
                    source=f"snapshot:{latest_snapshot.id}",
                    error=str(exc),
                ),
            }
        return {
            "printer_id": printer.id,
            "moonraker_url": printer.moonraker_url,
            **build_unreachable_health(printer.moonraker_url, str(exc)),
        }
    api_latency_ms = (time.perf_counter() - started_at) * 1000

    snapshots = snapshot_repository.list_snapshots_by_type(printer.id, "moonraker_status", limit=2)
    latest_diff = _latest_snapshot_diff(snapshot_repository, printer.id, snapshots)

    return {
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
            source=printer.moonraker_url,
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
        return await build_network_diagnostics(
            printer=printer,
            ssh_access=ssh_access,
            timeout_seconds=max(settings.request_timeout_seconds, settings.host_audit_timeout_seconds),
        )
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




@router.get("/api/printers/{printer_id}/updates/status")
async def printer_update_status(printer_id: int) -> UpdateStatusResponse:
    settings = get_settings()
    repository = get_printer_repository(settings)
    printer = repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")

    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    try:
        update_status = await client.update_status()
    except httpx.HTTPError as exc:
        return build_update_status({})
    return build_update_status(update_status)
