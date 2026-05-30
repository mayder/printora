from __future__ import annotations

from fastapi import Depends

from app.routes.auth import require_current_user_when_configured
from app.routes.support import *

router = APIRouter(dependencies=[Depends(require_current_user_when_configured)])


@router.get("/api/calibration/tests")
async def list_calibration_tests(category: str | None = None) -> dict[str, list[CalibrationTestRecord]]:
    settings = get_settings()
    repository = get_calibration_repository(settings)
    return {"tests": repository.list_tests(category)}




@router.get("/api/calibration/tests/{test_key}")
async def get_calibration_test(test_key: str) -> CalibrationTestRecord:
    settings = get_settings()
    repository = get_calibration_repository(settings)
    record = repository.get_test(test_key)
    if record is None:
        raise HTTPException(status_code=404, detail="calibration test not found")
    return record




@router.get("/api/printers/{printer_id}/calibration/available-tests")
async def list_available_calibration_tests(printer_id: int) -> CalibrationAvailableTestsResponse:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    connected = True
    try:
        available_objects = await client.printer_objects_list()
        object_payload = await client.printer_objects({"toolhead": ["axis_minimum", "axis_maximum"]}) if "toolhead" in available_objects else {}
    except httpx.HTTPError:
        connected = False
        available_objects = []
        object_payload = {}
    return build_available_calibration_tests(
        printer_id=printer.id,
        tests=repository.list_tests(),
        available_objects=available_objects,
        object_status=object_payload.get("status", object_payload) if isinstance(object_payload, dict) else {},
        connected=connected,
    )




@router.get("/api/printers/{printer_id}/calibration/runs")
async def list_calibration_runs(printer_id: int, limit: int = 50) -> dict[str, list[CalibrationRunRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    clean_limit = min(max(limit, 1), 100)
    return {"runs": repository.list_runs(printer_id, clean_limit)}




@router.get("/api/printers/{printer_id}/calibration/executions")
async def list_calibration_executions(printer_id: int, limit: int = 20) -> dict[str, list[CalibrationExecutionRecord]]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return {"executions": repository.list_execution_attempts(printer_id, limit=limit)}




@router.get("/api/printers/{printer_id}/calibration/summary")
async def calibration_summary(printer_id: int) -> CalibrationSummary:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.summary(printer_id)




@router.get("/api/printers/{printer_id}/calibration/sequence")
async def calibration_sequence(printer_id: int) -> CalibrationSequencePlan:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    return repository.sequence_plan(printer_id)




@router.get("/api/printers/{printer_id}/calibration/tests/{test_key}/preflight")
async def calibration_test_preflight(printer_id: int, test_key: str) -> CalibrationPreflight:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    test = repository.get_test(test_key)
    if test is None:
        raise HTTPException(status_code=404, detail="calibration test not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    preflight = await _operation_execution_preflight(client)
    return build_calibration_preflight(printer_id=printer.id, test=test, preflight=preflight)




@router.post("/api/printers/{printer_id}/calibration/runs")
async def create_calibration_run(printer_id: int, payload: CalibrationRunCreate) -> CalibrationRunRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        return repository.create_run(printer_id, payload)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc




@router.post("/api/printers/{printer_id}/calibration/execute")
async def execute_calibration_test(
    printer_id: int,
    payload: CalibrationExecutionRequest,
) -> CalibrationExecutionRecord:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    test = repository.get_test(payload.test_key)
    if test is None:
        raise HTTPException(status_code=404, detail="calibration test not found")
    client = MoonrakerClient(
        base_url=printer.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )
    preflight = await _operation_execution_preflight(client)
    gate = build_calibration_execution_gate(test=test, payload=payload, preflight=preflight)
    if gate.status == "blocked":
        return repository.create_execution_attempt(
            printer_id=printer.id,
            test=test,
            gate=gate,
            status="blocked",
            sent_commands=[],
            result=[],
            message=gate.message,
        )

    sent_commands: list[str] = []
    results: list[dict[str, Any]] = []
    failed_command: str | None = None
    for command in gate.commands:
        result = await _send_and_monitor_gcode(client, command, settings.request_timeout_seconds)
        results.append(result)
        if result.get("accepted"):
            sent_commands.append(command)
            continue
        failed_command = command
        break

    if failed_command is not None:
        status = "failed_partial" if sent_commands else "failed"
        failed_result = results[-1] if results else {}
        error_detail = str(failed_result.get("transport_error") or failed_result.get("monitor_error") or "sem detalhe")
        return repository.create_execution_attempt(
            printer_id=printer.id,
            test=test,
            gate=gate,
            status=status,
            sent_commands=sent_commands,
            result=results,
            message=f"Falha ao confirmar G-code '{failed_command}': {error_detail}",
        )

    return repository.create_execution_attempt(
        printer_id=printer.id,
        test=test,
        gate=gate,
        status="executed",
        sent_commands=sent_commands,
        result=results,
        message="G-code de calibração enviado e confirmado por monitoramento final do Moonraker.",
    )
