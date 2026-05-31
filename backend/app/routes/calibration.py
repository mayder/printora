from __future__ import annotations

from fastapi import Depends

from app.agent_executor import AgentCommandExecutor
from app.agent_moonraker import agent_preflight_payload, calibration_capabilities_payload
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
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_calibration_capabilities",
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
        available_objects, object_status, connected = calibration_capabilities_payload(job.result)
    except HTTPException:
        available_objects, object_status, connected = [], {}, False
    return build_available_calibration_tests(
        printer_id=printer.id,
        tests=repository.list_tests(),
        available_objects=available_objects,
        object_status=object_status,
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
    preflight = await _calibration_agent_preflight(settings, printer, test.test_key)
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
    preflight = await _calibration_agent_preflight(settings, printer, test.test_key)
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

    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_gcode_execute",
            payload={
                "action_id": f"calibration:{test.key}",
                "criticality": "calibration",
                "commands": gate.commands,
            },
            timeout_seconds=max(settings.request_timeout_seconds, 30.0),
        )
        result_payload = job.result or {}
        sent_commands = [str(item) for item in result_payload.get("sent_commands") or []]
        results = result_payload.get("results") if isinstance(result_payload.get("results"), list) else [result_payload]
    except HTTPException as exc:
        status = "failed"
        sent_commands = []
        results = [{"accepted": False, "agent_error": exc.detail}]
        error_detail = str(exc.detail)
        return repository.create_execution_attempt(
            printer_id=printer.id,
            test=test,
            gate=gate,
            status=status,
            sent_commands=sent_commands,
            result=results,
            message=f"Falha ao confirmar G-code pelo agente: {error_detail}",
        )

    return repository.create_execution_attempt(
        printer_id=printer.id,
        test=test,
        gate=gate,
        status="executed",
        sent_commands=sent_commands,
        result=results,
        message="G-code de calibração enviado pelo agente e confirmado.",
    )


async def _calibration_agent_preflight(settings, printer, test_key: str) -> dict[str, Any]:
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_gcode_preflight",
            payload={"action_id": f"calibration:{test_key}", "criticality": "calibration"},
            timeout_seconds=max(settings.request_timeout_seconds, 10.0),
        )
    except HTTPException as exc:
        return {
            "safe_mode": "agent_preflight",
            "connected": False,
            "printing": False,
            "print_state": "",
            "summary": "Agente indisponível no preflight.",
            "error": str(exc.detail),
            "source": "agent",
        }
    return agent_preflight_payload(job.result)
