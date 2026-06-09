from __future__ import annotations

import re

from fastapi import Depends, Header

from app.agent_executor import AgentCommandExecutor, AgentJobFailedError
from app.agent_moonraker import agent_preflight_payload, calibration_capabilities_payload
from app.auth import AuthRepository
from app.config_remediation import (
    ConfigRemediationApplyRequest,
    ConfigRemediationRequest,
    build_config_remediation_script,
    parse_config_remediation_stdout,
)
from app.routes.auth import require_current_user, require_current_user_when_configured
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


@router.delete("/api/printers/{printer_id}/calibration/executions/{attempt_id}")
async def delete_calibration_execution(printer_id: int, attempt_id: int) -> dict[str, bool]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        deleted = repository.delete_execution_attempt_if_not_latest(printer_id, attempt_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="calibration execution not found")
    return {"deleted": True}


@router.delete("/api/printers/{printer_id}/calibration/runs/{run_id}")
async def delete_calibration_run(printer_id: int, run_id: int) -> dict[str, bool]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    repository = get_calibration_repository(settings)
    if printer_repository.get_printer(printer_id) is None:
        raise HTTPException(status_code=404, detail="printer not found")
    try:
        deleted = repository.delete_run_if_not_latest(printer_id, run_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(status_code=404, detail="calibration run not found")
    return {"deleted": True}


@router.post("/api/printers/{printer_id}/calibration/config-remediation/preview")
async def preview_calibration_config_remediation(printer_id: int, payload: ConfigRemediationRequest) -> dict[str, Any]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    result = await _run_config_remediation_script(
        settings,
        printer,
        payload,
        mode="preview",
        timeout_seconds=max(settings.request_timeout_seconds, 15.0),
    )
    return {"printer_id": printer.id, **result}


@router.post("/api/printers/{printer_id}/calibration/config-remediation/apply")
async def apply_calibration_config_remediation(
    printer_id: int,
    payload: ConfigRemediationApplyRequest,
    authorization: str | None = Header(default=None),
) -> dict[str, Any]:
    settings = get_settings()
    printer_repository = get_printer_repository(settings)
    printer = printer_repository.get_printer(printer_id)
    if printer is None:
        raise HTTPException(status_code=404, detail="printer not found")
    _require_config_remediation_step_up(settings, authorization, payload.step_up_token)
    result = await _run_config_remediation_script(
        settings,
        printer,
        payload,
        mode="apply",
        timeout_seconds=max(settings.request_timeout_seconds, 20.0),
    )
    if result.get("status") == "applied":
        result["firmware_restart"] = await _restart_firmware_after_config_remediation(settings, printer)
    return {"printer_id": printer.id, **result}




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
    recent_execution = repository.recent_sent_execution(printer.id, test.test_key)
    if recent_execution is not None:
        return repository.create_execution_attempt(
            printer_id=printer.id,
            test=test,
            gate=gate,
            status="blocked",
            sent_commands=[],
            result=[
                {
                    "blocked_duplicate_of": recent_execution.id,
                    "last_execution_at": recent_execution.created_at,
                    "last_sent_commands": recent_execution.sent_commands,
                }
            ],
            message="Execução repetida bloqueada por segurança; aguarde alguns segundos antes de repetir o mesmo teste.",
        )

    try:
        command_timeout = _calibration_execution_timeout(test, settings)
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_gcode_execute",
            payload={
                "action_id": f"calibration:{test.test_key}",
                "criticality": "calibration",
                "commands": gate.commands,
                "timeout_seconds": command_timeout,
            },
            timeout_seconds=command_timeout + 20.0,
        )
        result_payload = job.result or {}
        sent_commands = [str(item) for item in result_payload.get("sent_commands") or []]
        results = _calibration_execution_results(result_payload)
        execution_status = str(result_payload.get("status") or "executed")
        if execution_status not in {"executed", "dispatched_unconfirmed", "failed_partial"}:
            execution_status = "executed"
    except AgentJobFailedError as exc:
        result_payload = exc.job.result or {"agent_error": exc.detail}
        sent_commands = [str(item) for item in result_payload.get("sent_commands") or []]
        results = _calibration_execution_results(result_payload)
        if not results:
            results = [{"accepted": False, "agent_error": exc.detail}]
        error_detail = _calibration_agent_failure_detail(result_payload) or str(exc.detail)
        return repository.create_execution_attempt(
            printer_id=printer.id,
            test=test,
            gate=gate,
            status="failed",
            sent_commands=sent_commands,
            result=results,
            message=f"Falha ao confirmar G-code pelo agente: {error_detail}",
        )
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
        status=execution_status,
        sent_commands=sent_commands,
        result=results,
        message=_calibration_execution_message(execution_status, sent_commands, gate.commands),
    )


def _calibration_agent_failure_detail(payload: dict) -> str:
    for message in payload.get("console_excerpt") or []:
        text = str(message).strip()
        if "SAVE_CONFIG" in text or "conflicts with included value" in text:
            return text
    detail = payload.get("detail") or payload.get("agent_error")
    return str(detail).strip() if detail else ""


async def _run_config_remediation_script(settings, printer, payload, *, mode: str, timeout_seconds: float) -> dict[str, Any]:
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_host_script",
            payload={
                "kind": f"config_remediation_{mode}",
                "script": build_config_remediation_script(payload, mode=mode),
                "timeout_seconds": timeout_seconds,
            },
            timeout_seconds=timeout_seconds + 5.0,
        )
    except AgentJobFailedError as exc:
        result = exc.job.result if isinstance(exc.job.result, dict) else {}
        stdout = str(result.get("stdout") or "")
        parsed = parse_config_remediation_stdout(stdout)
        parsed.setdefault("status", "failed")
        parsed.setdefault("error", exc.detail)
        return parsed
    except HTTPException as exc:
        return {"status": "failed", "error": str(exc.detail)}
    result = job.result if isinstance(job.result, dict) else {}
    parsed = parse_config_remediation_stdout(str(result.get("stdout") or ""))
    if result.get("exit_code") not in (0, None):
        parsed.setdefault("status", "failed")
        parsed.setdefault("error", str(result.get("stderr") or result.get("error") or "script remoto falhou"))
    return parsed


async def _restart_firmware_after_config_remediation(settings, printer) -> dict[str, Any]:
    try:
        job = await AgentCommandExecutor(settings.database_path).run(
            printer,
            job_type="remote_gcode_execute",
            payload={
                "action_id": "config_remediation:firmware_restart",
                "criticality": "config_remediation",
                "commands": ["FIRMWARE_RESTART"],
                "timeout_seconds": max(settings.request_timeout_seconds, 20.0),
            },
            timeout_seconds=max(settings.request_timeout_seconds, 25.0),
        )
        return job.result or {"status": "executed"}
    except AgentJobFailedError as exc:
        return exc.job.result or {"status": "failed", "detail": exc.detail}
    except HTTPException as exc:
        return {"status": "failed", "detail": str(exc.detail)}


def _require_config_remediation_step_up(settings, authorization: str | None, step_up_token: str | None) -> None:
    if not authorization:
        return
    repository = AuthRepository(settings.database_path)
    current = require_current_user(authorization=authorization, repository=repository)
    if not step_up_token or not repository.consume_step_up(current.user.id, step_up_token, "destructive_action"):
        raise HTTPException(status_code=403, detail="autenticação reforçada obrigatória para ação crítica")


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


def _calibration_execution_message(status: str, sent_commands: list[str], commands: list[str]) -> str:
    if status == "dispatched_unconfirmed":
        return (
            f"{len(sent_commands)}/{len(commands)} comando(s) despachado(s), mas o Moonraker nao confirmou "
            "a resposta dentro do timeout. Confira a impressora antes de repetir."
        )
    if status == "failed_partial":
        return f"{len(sent_commands)}/{len(commands)} comando(s) confirmado(s); execucao parcial."
    return f"{len(sent_commands)}/{len(commands)} comando(s) confirmado(s)."


def _calibration_execution_timeout(test, settings) -> float:
    command_text = "\n".join(test.gcode).upper()
    if "PID_CALIBRATE" in command_text:
        return max(settings.request_timeout_seconds, 140.0)
    if "BED_MESH_CALIBRATE" in command_text or "QUAD_GANTRY_LEVEL" in command_text or "PROBE_ACCURACY" in command_text:
        return max(settings.request_timeout_seconds, 90.0)
    return max(settings.request_timeout_seconds, 45.0)


def _calibration_execution_results(result_payload: dict[str, Any]) -> list[dict[str, Any]]:
    raw_results = result_payload.get("results")
    results = [item for item in raw_results if isinstance(item, dict)] if isinstance(raw_results, list) else [result_payload]
    console_excerpt = [str(item) for item in result_payload.get("console_excerpt") or [] if str(item).strip()]
    if console_excerpt:
        results.append(
            {
                "kind": "moonraker_console",
                "console_excerpt": console_excerpt,
                "save_config_required": _console_requires_save_config(console_excerpt),
                "pid_parameters": _extract_pid_parameters(console_excerpt),
            }
        )
    return results


def _console_requires_save_config(console_excerpt: list[str]) -> bool:
    return "SAVE_CONFIG" in "\n".join(console_excerpt).upper()


def _extract_pid_parameters(console_excerpt: list[str]) -> dict[str, float] | None:
    match = re.search(
        r"pid_Kp=(?P<kp>[0-9.]+)\s+pid_Ki=(?P<ki>[0-9.]+)\s+pid_Kd=(?P<kd>[0-9.]+)",
        "\n".join(console_excerpt),
    )
    if not match:
        return None
    return {
        "pid_Kp": float(match.group("kp")),
        "pid_Ki": float(match.group("ki")),
        "pid_Kd": float(match.group("kd")),
    }
