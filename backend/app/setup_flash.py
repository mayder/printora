from __future__ import annotations

import asyncio
import json
import os
import re
import shlex
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.database import connect_database
from app.setup_firmware import _line_value, _parse_output_sections, _trim
from app.setup_wizard import SetupCommandPlan, SetupSshTarget, _target_label


FLASH_MODE_ENV = "PRINTORA_REMOTE_FLASH_MODE"
SetupFlashStatus = Literal["ok", "warning", "error", "blocked", "requires_recovery"]
SetupFlashMethod = Literal["can_katapult", "usb_dfu", "manual"]
SetupFlashRole = Literal["mainboard", "toolhead", "can_adapter", "unknown"]


class SetupFlashRequest(BaseModel):
    target: SetupSshTarget
    board_name: str = Field(min_length=1, max_length=120)
    board_role: SetupFlashRole = "unknown"
    flash_method: SetupFlashMethod = "can_katapult"
    artifact_path: str = Field(min_length=1, max_length=300)
    can_interface: str = Field(default="can0", min_length=3, max_length=24)
    expected_uuid: str | None = Field(default=None, max_length=80)
    klipper_path: str = Field(default="~/klipper", min_length=1, max_length=220)
    previous_binary_path: str | None = Field(default=None, max_length=300)
    checklist_confirmed: bool = False

    @field_validator("can_interface")
    @classmethod
    def _validate_interface(cls, value: str) -> str:
        cleaned = value.strip()
        if not re.fullmatch(r"[a-zA-Z0-9_.:-]+", cleaned):
            raise ValueError("can_interface inválida")
        return cleaned

    @field_validator("expected_uuid")
    @classmethod
    def _validate_uuid(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{8,32}", cleaned):
            raise ValueError("expected_uuid inválido")
        return cleaned


class SetupFlashExecuteRequest(SetupFlashRequest):
    confirmation: str = Field(min_length=1, max_length=120)


class SetupFlashFinding(BaseModel):
    key: str
    status: SetupFlashStatus
    title: str
    detail: str
    action: str


class SetupFlashPreflightResponse(BaseModel):
    safe_mode: str
    connected: bool
    status: SetupFlashStatus
    target: str
    board_name: str
    board_role: SetupFlashRole
    flash_method: SetupFlashMethod
    artifact_path: str
    artifact_sha256: str | None = None
    expected_uuid: str | None = None
    summary: str
    findings: list[SetupFlashFinding]
    sections: dict[str, str]
    parsed: dict[str, object]
    rollback: list[str]
    history_id: int | None = None
    error: str | None = None


class SetupFlashPlanStep(BaseModel):
    key: str
    title: str
    status: Literal["ready", "missing", "manual", "blocked"]
    detail: str
    commands: list[SetupCommandPlan] = Field(default_factory=list)
    rollback: str | None = None


class SetupFlashPlanResponse(BaseModel):
    safe_mode: str
    status: SetupFlashStatus
    target: str
    board_name: str
    board_role: SetupFlashRole
    flash_method: SetupFlashMethod
    artifact_path: str
    artifact_sha256: str | None = None
    expected_uuid: str | None = None
    confirmation_phrase: str
    summary: str
    preflight: SetupFlashPreflightResponse
    steps: list[SetupFlashPlanStep]
    blocked_reasons: list[str]
    rollback: list[str]
    history_id: int | None = None


class SetupFlashExecuteResponse(BaseModel):
    safe_mode: str
    status: SetupFlashStatus
    target: str
    board_name: str
    board_role: SetupFlashRole
    flash_method: SetupFlashMethod
    artifact_path: str
    artifact_sha256: str | None = None
    expected_uuid: str | None = None
    summary: str
    command_log: str
    duration_ms: int | None = None
    post_validation: SetupFlashPreflightResponse | None = None
    rollback: list[str]
    blocked_reasons: list[str] = Field(default_factory=list)
    history_id: int | None = None


class SetupFlashRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_type: Literal["preflight", "plan", "flash"]
    status: SetupFlashStatus
    safe_mode: str
    target_host: str
    target_port: int
    target_user: str
    board_name: str
    board_role: SetupFlashRole
    flash_method: SetupFlashMethod
    can_interface: str | None
    expected_uuid: str | None
    artifact_path: str
    artifact_sha256: str | None
    previous_binary_path: str | None
    confirmation_phrase: str | None
    duration_ms: int | None
    summary: dict[str, object]
    preflight: dict[str, object] | None
    plan: dict[str, object] | None
    command_log: str | None
    rollback: list[str]
    error_message: str | None
    created_at: str


@dataclass(frozen=True)
class SetupFlashRunRepository:
    database_path: Path

    def create_preflight(self, request: SetupFlashRequest, response: SetupFlashPreflightResponse) -> int:
        return self._create_run(
            run_type="preflight",
            request=request,
            status=response.status,
            safe_mode=response.safe_mode,
            artifact_sha256=response.artifact_sha256,
            confirmation_phrase=None,
            duration_ms=None,
            summary={"summary": response.summary, "findings": [finding.model_dump() for finding in response.findings]},
            preflight={"sections": response.sections, "parsed": response.parsed},
            plan=None,
            command_log=None,
            rollback=response.rollback,
            error=response.error,
        )

    def create_plan(self, request: SetupFlashRequest, response: SetupFlashPlanResponse) -> int:
        return self._create_run(
            run_type="plan",
            request=request,
            status=response.status,
            safe_mode=response.safe_mode,
            artifact_sha256=response.artifact_sha256,
            confirmation_phrase=response.confirmation_phrase,
            duration_ms=None,
            summary={"summary": response.summary, "blocked_reasons": response.blocked_reasons},
            preflight={"status": response.preflight.status, "summary": response.preflight.summary},
            plan={"steps": [step.model_dump() for step in response.steps]},
            command_log=None,
            rollback=response.rollback,
            error="; ".join(response.blocked_reasons) if response.blocked_reasons else None,
        )

    def create_flash(self, request: SetupFlashRequest, response: SetupFlashExecuteResponse) -> int:
        return self._create_run(
            run_type="flash",
            request=request,
            status=response.status,
            safe_mode=response.safe_mode,
            artifact_sha256=response.artifact_sha256,
            confirmation_phrase=confirmation_phrase(request),
            duration_ms=response.duration_ms,
            summary={"summary": response.summary, "blocked_reasons": response.blocked_reasons},
            preflight={"post_validation": response.post_validation.model_dump() if response.post_validation else None},
            plan=None,
            command_log=response.command_log,
            rollback=response.rollback,
            error="; ".join(response.blocked_reasons) if response.blocked_reasons else None,
        )

    def list_runs(self, limit: int = 20) -> list[SetupFlashRunRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, run_type, status, safe_mode, target_host, target_port, target_user,
                       board_name, board_role, flash_method, can_interface, expected_uuid,
                       artifact_path, artifact_sha256, previous_binary_path, confirmation_phrase,
                       duration_ms, summary_json, preflight_json, plan_json, command_log,
                       rollback_json, error_message, created_at
                FROM setup_flash_runs
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [_run_from_row(row) for row in rows]

    def _create_run(
        self,
        *,
        run_type: Literal["preflight", "plan", "flash"],
        request: SetupFlashRequest,
        status: SetupFlashStatus,
        safe_mode: str,
        artifact_sha256: str | None,
        confirmation_phrase: str | None,
        duration_ms: int | None,
        summary: dict[str, object],
        preflight: dict[str, object] | None,
        plan: dict[str, object] | None,
        command_log: str | None,
        rollback: list[str],
        error: str | None,
    ) -> int:
        target = request.target
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO setup_flash_runs (
                    run_type, status, safe_mode, target_host, target_port, target_user,
                    board_name, board_role, flash_method, can_interface, expected_uuid,
                    artifact_path, artifact_sha256, previous_binary_path, confirmation_phrase,
                    duration_ms, summary_json, preflight_json, plan_json, command_log,
                    rollback_json, error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_type,
                    status,
                    safe_mode,
                    target.host,
                    target.port,
                    target.username,
                    request.board_name,
                    request.board_role,
                    request.flash_method,
                    request.can_interface,
                    request.expected_uuid,
                    request.artifact_path,
                    artifact_sha256,
                    request.previous_binary_path,
                    confirmation_phrase,
                    duration_ms,
                    json.dumps(summary, ensure_ascii=False),
                    json.dumps(preflight, ensure_ascii=False) if preflight is not None else None,
                    json.dumps(plan, ensure_ascii=False) if plan is not None else None,
                    command_log,
                    json.dumps(rollback, ensure_ascii=False),
                    error,
                ),
            )
            return int(cursor.lastrowid)


async def run_setup_flash_preflight(request: SetupFlashRequest) -> SetupFlashPreflightResponse:
    script = _remote_preflight_script(request)
    result = await _run_remote_script(request.target, script, timeout_seconds=max(request.target.timeout_seconds, 20.0))
    if result["error"]:
        return _connection_error_preflight(request, str(result["error"]))
    output = f"{result['stdout']}\n{result['stderr']}"
    if int(result["exit_code"] or 0) != 0:
        return _connection_error_preflight(request, f"exit_code={result['exit_code']}", output)
    sections = _parse_output_sections(str(result["stdout"]))
    parsed = _parse_preflight_sections(request, sections)
    findings = _flash_findings(request, parsed)
    status = _findings_status(findings)
    return SetupFlashPreflightResponse(
        safe_mode="flash_preflight_read_only",
        connected=True,
        status=status,
        target=_target_label(request.target),
        board_name=request.board_name,
        board_role=request.board_role,
        flash_method=request.flash_method,
        artifact_path=request.artifact_path,
        artifact_sha256=parsed.get("artifact_sha256") if isinstance(parsed.get("artifact_sha256"), str) else None,
        expected_uuid=request.expected_uuid,
        summary="Preflight de flash aprovado." if status == "ok" else "Preflight de flash requer atenção.",
        findings=findings,
        sections={key: _trim(value, 3000) for key, value in sections.items()},
        parsed=parsed,
        rollback=rollback_steps(request),
    )


async def build_setup_flash_plan(request: SetupFlashRequest) -> SetupFlashPlanResponse:
    preflight = await run_setup_flash_preflight(request)
    blocked = _blocked_reasons(request, preflight)
    phrase = confirmation_phrase(request)
    steps = _plan_steps(request, preflight, phrase, blocked)
    return SetupFlashPlanResponse(
        safe_mode="flash_supervised_plan_only",
        status="blocked" if blocked else "ok",
        target=_target_label(request.target),
        board_name=request.board_name,
        board_role=request.board_role,
        flash_method=request.flash_method,
        artifact_path=request.artifact_path,
        artifact_sha256=preflight.artifact_sha256,
        expected_uuid=request.expected_uuid,
        confirmation_phrase=phrase,
        summary="Plano de flash bloqueado." if blocked else "Plano de flash supervisionado pronto.",
        preflight=preflight,
        steps=steps,
        blocked_reasons=blocked,
        rollback=rollback_steps(request),
    )


async def execute_setup_flash(request: SetupFlashExecuteRequest) -> SetupFlashExecuteResponse:
    phrase = confirmation_phrase(request)
    if request.confirmation != phrase:
        return _blocked_execute(request, ["Confirmação textual inválida."], "")
    if os.getenv(FLASH_MODE_ENV) != "remote":
        return _blocked_execute(request, [f"{FLASH_MODE_ENV}=remote não está habilitado."], "")
    plan = await build_setup_flash_plan(request)
    if plan.blocked_reasons:
        return _blocked_execute(request, plan.blocked_reasons, "")
    started = time.monotonic()
    result = await _run_remote_script(
        request.target,
        _remote_flash_script(request),
        timeout_seconds=max(request.target.timeout_seconds, 120.0),
    )
    duration_ms = int((time.monotonic() - started) * 1000)
    command_log = _trim(f"{result['stdout']}\n{result['stderr']}", 12000)
    if result["error"]:
        return _requires_recovery(request, str(result["error"]), command_log, duration_ms)
    if int(result["exit_code"] or 0) != 0:
        return _requires_recovery(request, f"exit_code={result['exit_code']}", command_log, duration_ms)
    sections = _parse_output_sections(str(result["stdout"]))
    artifact_sha = _line_value(sections.get("artifact", ""), "artifact_sha256") or plan.artifact_sha256
    post_validation = await run_setup_flash_preflight(request)
    status: SetupFlashStatus = "ok" if post_validation.status in ("ok", "warning") else "requires_recovery"
    reasons = [] if status == "ok" else ["Validação pós-flash não confirmou o estado esperado."]
    return SetupFlashExecuteResponse(
        safe_mode="flash_supervised_can_katapult",
        status=status,
        target=_target_label(request.target),
        board_name=request.board_name,
        board_role=request.board_role,
        flash_method=request.flash_method,
        artifact_path=request.artifact_path,
        artifact_sha256=artifact_sha,
        expected_uuid=request.expected_uuid,
        summary="Flash supervisionado concluído." if status == "ok" else "Flash executado, mas requer recuperação manual.",
        command_log=command_log,
        duration_ms=duration_ms,
        post_validation=post_validation,
        rollback=rollback_steps(request),
        blocked_reasons=reasons,
    )


def confirmation_phrase(request: SetupFlashRequest) -> str:
    board = re.sub(r"[^A-Z0-9]+", "_", request.board_name.upper()).strip("_") or "BOARD"
    method = request.flash_method.upper()
    return f"FLASH_{board}_{method}"


def rollback_steps(request: SetupFlashRequest) -> list[str]:
    steps = [
        "Não reiniciar a impressora em loop; registrar estado atual e log do flash.",
        "Colocar a placa novamente em bootloader/Katapult conforme manual físico da placa.",
        f"Reexecutar o flash anterior usando o método {request.flash_method} com o binário anterior validado.",
        "Validar UUID/serial e somente depois reiniciar Klipper/Moonraker se necessário.",
    ]
    if request.previous_binary_path:
        steps.insert(2, f"Binário anterior informado: {request.previous_binary_path}.")
    return steps


def _remote_preflight_script(request: SetupFlashRequest) -> str:
    artifact = shlex.quote(request.artifact_path)
    klipper = shlex.quote(request.klipper_path.rstrip("/"))
    iface = shlex.quote(request.can_interface)
    uuid = shlex.quote(request.expected_uuid or "")
    return f"""set +e
ARTIFACT_PATH={artifact}
KLIPPER_PATH={klipper}
CAN_IFACE={iface}
EXPECTED_UUID={uuid}
expand_path() {{
  case "$1" in
    "~") printf '%s\\n' "$HOME" ;;
    "~/"*) printf '%s/%s\\n' "$HOME" "${{1#~/}}" ;;
    *) printf '%s\\n' "$1" ;;
  esac
}}
ARTIFACT_PATH="$(expand_path "$ARTIFACT_PATH")"
KLIPPER_PATH="$(expand_path "$KLIPPER_PATH")"
printf 'SECTION tools\\n'
for tool in test sha256sum stat timeout curl python3; do
  if command -v "$tool" >/dev/null 2>&1; then printf '%s=present:%s\\n' "$tool" "$(command -v "$tool")"; else printf '%s=missing\\n' "$tool"; fi
done
printf '\\nSECTION artifact\\n'
if [ -f "$ARTIFACT_PATH" ]; then
  printf 'artifact_exists=yes\\n'
  printf 'artifact_size=%s\\n' "$(stat -c %s "$ARTIFACT_PATH" 2>/dev/null || wc -c < "$ARTIFACT_PATH")"
  printf 'artifact_sha256=%s\\n' "$(sha256sum "$ARTIFACT_PATH" 2>/dev/null | awk '{{print $1}}')"
else
  printf 'artifact_exists=no\\n'
fi
printf '\\nSECTION print_state\\n'
if command -v curl >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
  curl -fsS 'http://127.0.0.1:7125/printer/objects/query?print_stats' 2>/dev/null | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("result",{{}}).get("status",{{}}).get("print_stats",{{}}).get("state","unknown"))' 2>/dev/null || printf 'unknown\\n'
else
  printf 'unknown\\n'
fi
printf '\\nSECTION flash_tool\\n'
if [ -f "$KLIPPER_PATH/scripts/flash_can.py" ]; then printf 'flash_can=present:%s/scripts/flash_can.py\\n' "$KLIPPER_PATH"; else printf 'flash_can=missing\\n'; fi
if [ -x "$HOME/klippy-env/bin/python" ]; then printf 'klippy_python=present:%s/klippy-env/bin/python\\n' "$HOME"; else printf 'klippy_python=missing\\n'; fi
printf '\\nSECTION uuid_query\\n'
if [ -x "$HOME/klippy-env/bin/python" ] && [ -f "$KLIPPER_PATH/scripts/canbus_query.py" ]; then
  timeout 8 "$HOME/klippy-env/bin/python" "$KLIPPER_PATH/scripts/canbus_query.py" "$CAN_IFACE" 2>&1
else
  printf 'canbus_query_unavailable\\n'
fi
printf '\\nSECTION printer_info\\n'
curl -fsS 'http://127.0.0.1:7125/printer/info' 2>/dev/null | head -c 1200 || printf 'printer_info_unavailable\\n'
"""


def _remote_flash_script(request: SetupFlashRequest) -> str:
    artifact = shlex.quote(request.artifact_path)
    klipper = shlex.quote(request.klipper_path.rstrip("/"))
    iface = shlex.quote(request.can_interface)
    uuid = shlex.quote(request.expected_uuid or "")
    return f"""set -euo pipefail
ARTIFACT_PATH={artifact}
KLIPPER_PATH={klipper}
CAN_IFACE={iface}
EXPECTED_UUID={uuid}
expand_path() {{
  case "$1" in
    "~") printf '%s\\n' "$HOME" ;;
    "~/"*) printf '%s/%s\\n' "$HOME" "${{1#~/}}" ;;
    *) printf '%s\\n' "$1" ;;
  esac
}}
ARTIFACT_PATH="$(expand_path "$ARTIFACT_PATH")"
KLIPPER_PATH="$(expand_path "$KLIPPER_PATH")"
BACKUP_ROOT="$HOME/.local/share/printora/flash-setup/backups"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
RUN_DIR="$BACKUP_ROOT/$STAMP"
printf 'SECTION preflight\\n'
test -f "$ARTIFACT_PATH"
test -n "$EXPECTED_UUID"
test -f "$KLIPPER_PATH/scripts/flash_can.py"
test -x "$HOME/klippy-env/bin/python"
STATE="$(curl -fsS 'http://127.0.0.1:7125/printer/objects/query?print_stats' 2>/dev/null | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("result",{{}}).get("status",{{}}).get("print_stats",{{}}).get("state","unknown"))' 2>/dev/null || true)"
printf 'print_state=%s\\n' "$STATE"
case "$STATE" in printing|paused) printf 'blocked_printing=yes\\n'; exit 23 ;; esac
mkdir -p "$RUN_DIR"
cp "$ARTIFACT_PATH" "$RUN_DIR/$(basename "$ARTIFACT_PATH").before-flash"
printf '\\nSECTION artifact\\n'
printf 'backup_artifact=%s\\n' "$RUN_DIR/$(basename "$ARTIFACT_PATH").before-flash"
printf 'artifact_sha256=%s\\n' "$(sha256sum "$ARTIFACT_PATH" | awk '{{print $1}}')"
printf '\\nSECTION flash\\n'
set +e
timeout 90 "$HOME/klippy-env/bin/python" "$KLIPPER_PATH/scripts/flash_can.py" -i "$CAN_IFACE" -f "$ARTIFACT_PATH" -u "$EXPECTED_UUID" 2>&1 | tee "$RUN_DIR/flash.log"
FLASH_STATUS="${{PIPESTATUS[0]}}"
set -e
printf 'flash_exit_code=%s\\n' "$FLASH_STATUS"
test "$FLASH_STATUS" = "0"
printf '\\nSECTION post_uuid_query\\n'
timeout 8 "$HOME/klippy-env/bin/python" "$KLIPPER_PATH/scripts/canbus_query.py" "$CAN_IFACE" 2>&1 || true
printf '\\nSECTION printer_info\\n'
curl -fsS 'http://127.0.0.1:7125/printer/info' 2>/dev/null | head -c 1200 || true
"""


async def _run_remote_script(target: SetupSshTarget, script: str, timeout_seconds: float) -> dict[str, object]:
    command = _ssh_command(target)
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
    except FileNotFoundError:
        return {"stdout": "", "stderr": "", "exit_code": None, "error": "Comando ssh não encontrado no host do Printora."}
    except OSError as exc:
        return {"stdout": "", "stderr": "", "exit_code": None, "error": str(exc)}
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(process.communicate(script.encode()), timeout=timeout_seconds)
    except TimeoutError:
        process.kill()
        await process.wait()
        return {"stdout": "", "stderr": "", "exit_code": None, "error": f"Timeout de SSH após {timeout_seconds:.0f}s."}
    return {
        "stdout": stdout_bytes.decode(errors="replace"),
        "stderr": stderr_bytes.decode(errors="replace"),
        "exit_code": process.returncode,
        "error": None,
    }


def _ssh_command(target: SetupSshTarget) -> list[str]:
    command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        f"ConnectTimeout={max(1, int(target.timeout_seconds))}",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-o",
        "LogLevel=ERROR",
        "-p",
        str(target.port),
    ]
    if target.auth_method == "key_path" and target.key_path:
        command.extend(["-i", str(Path(target.key_path).expanduser())])
    command.extend([f"{target.username}@{target.host}", "bash -s"])
    return command


def _parse_preflight_sections(request: SetupFlashRequest, sections: dict[str, str]) -> dict[str, object]:
    artifact = sections.get("artifact", "")
    uuid_query = sections.get("uuid_query", "")
    print_state = sections.get("print_state", "").strip().splitlines()[0] if sections.get("print_state", "").strip() else "unknown"
    canbus_uuids = [uuid.lower() for uuid in re.findall(r"canbus_uuid=([0-9a-fA-F]+)", uuid_query)]
    return {
        "artifact_exists": _line_value(artifact, "artifact_exists") == "yes",
        "artifact_sha256": _line_value(artifact, "artifact_sha256"),
        "print_state": print_state,
        "flash_can_present": "flash_can=present" in sections.get("flash_tool", ""),
        "klippy_python_present": "klippy_python=present" in sections.get("flash_tool", ""),
        "canbus_uuids": canbus_uuids,
        "expected_uuid_visible": bool(request.expected_uuid and request.expected_uuid.lower() in canbus_uuids),
    }


def _flash_findings(request: SetupFlashRequest, parsed: dict[str, object]) -> list[SetupFlashFinding]:
    findings = [
        SetupFlashFinding(
            key="checklist",
            status="ok" if request.checklist_confirmed else "blocked",
            title="Checklist físico",
            detail="Checklist crítico confirmado." if request.checklist_confirmed else "Confirme alimentação, placa, bootloader, cabo e binário antes do flash.",
            action="Marcar checklist somente depois da conferência física.",
        ),
        SetupFlashFinding(
            key="artifact",
            status="ok" if parsed["artifact_exists"] else "blocked",
            title="Artefato de firmware",
            detail=f"Artefato encontrado com sha256 {str(parsed.get('artifact_sha256') or '')[:12]}." if parsed["artifact_exists"] else "Artefato remoto não encontrado.",
            action="Use o binário gerado pelo build remoto ou informe um caminho válido na Pi.",
        ),
        SetupFlashFinding(
            key="print_state",
            status="blocked" if parsed["print_state"] in ("printing", "paused") else "ok",
            title="Impressão parada",
            detail=f"Estado reportado: {parsed['print_state']}.",
            action="Cancelar/aguardar impressão antes de qualquer flash.",
        ),
    ]
    if request.flash_method == "can_katapult":
        findings.extend(
            [
                SetupFlashFinding(
                    key="method_supported",
                    status="ok",
                    title="Método CAN/Katapult",
                    detail="Método inicial suportado pelo fluxo de flash supervisionado.",
                    action="Manter placa em bootloader Katapult e UUID visível.",
                ),
                SetupFlashFinding(
                    key="flash_tool",
                    status="ok" if parsed["flash_can_present"] and parsed["klippy_python_present"] else "blocked",
                    title="Ferramentas de flash",
                    detail="flash_can.py e klippy-env encontrados." if parsed["flash_can_present"] and parsed["klippy_python_present"] else "flash_can.py ou klippy-env ausente.",
                    action="Instalar/validar Klipper no host remoto antes do flash.",
                ),
                SetupFlashFinding(
                    key="uuid",
                    status="ok" if parsed["expected_uuid_visible"] else "blocked",
                    title="UUID em bootloader",
                    detail=f"UUID {request.expected_uuid} visível no barramento." if parsed["expected_uuid_visible"] else "UUID esperado não está visível no canbus_query.",
                    action="Colocar a placa correta em bootloader Katapult e repetir preflight.",
                ),
            ]
        )
    else:
        findings.append(
            SetupFlashFinding(
                key="method_supported",
                status="blocked",
                title="Método ainda não suportado",
                detail="A execução real está disponível apenas para CAN/Katapult.",
                action="Usar plano manual ou implementar método específico em outro lote.",
            )
        )
    return findings


def _findings_status(findings: list[SetupFlashFinding]) -> SetupFlashStatus:
    if any(finding.status == "blocked" for finding in findings):
        return "blocked"
    if any(finding.status == "warning" for finding in findings):
        return "warning"
    return "ok"


def _blocked_reasons(request: SetupFlashRequest, preflight: SetupFlashPreflightResponse) -> list[str]:
    reasons = [finding.detail for finding in preflight.findings if finding.status == "blocked"]
    if request.flash_method != "can_katapult":
        reasons.append("Execução real deste método ainda não é suportada.")
    if request.flash_method == "can_katapult" and not request.expected_uuid:
        reasons.append("UUID esperado é obrigatório para flash CAN/Katapult.")
    return list(dict.fromkeys(reasons))


def _plan_steps(
    request: SetupFlashRequest,
    preflight: SetupFlashPreflightResponse,
    phrase: str,
    blocked: list[str],
) -> list[SetupFlashPlanStep]:
    status = "blocked" if blocked else "ready"
    command = (
        f"PLAN ~/klippy-env/bin/python {request.klipper_path.rstrip('/')}/scripts/flash_can.py "
        f"-i {request.can_interface} -f {request.artifact_path} -u {request.expected_uuid or '<uuid>'}"
    )
    return [
        SetupFlashPlanStep(
            key="preflight",
            title="Preflight read-only",
            status="ready" if preflight.status == "ok" else "blocked",
            detail=preflight.summary,
            commands=[SetupCommandPlan(command="PLAN validar artifact, print_stats, flash_can.py e canbus_query", risk="read_only", reason="Não altera placa ou configuração.")],
        ),
        SetupFlashPlanStep(
            key="flash_command",
            title="Comando de flash",
            status=status,
            detail=f"Execução permitida somente com confirmação {phrase} e {FLASH_MODE_ENV}=remote.",
            commands=[SetupCommandPlan(command=command, risk="mutable", reason="Grava firmware na MCU via CAN/Katapult.")],
            rollback="Usar o binário anterior e repetir o mesmo método com a placa em bootloader.",
        ),
        SetupFlashPlanStep(
            key="post_validation",
            title="Validação pós-flash",
            status=status,
            detail="Reconsulta UUID/CAN e printer/info; não edita printer.cfg e não reinicia serviços.",
            commands=[SetupCommandPlan(command=f"PLAN ~/klippy-env/bin/python ~/klipper/scripts/canbus_query.py {request.can_interface}", risk="read_only", reason="Confirma visibilidade da placa após flash.")],
        ),
    ]


def _connection_error_preflight(request: SetupFlashRequest, error: str, command_log: str = "") -> SetupFlashPreflightResponse:
    return SetupFlashPreflightResponse(
        safe_mode="flash_preflight_read_only",
        connected=False,
        status="error",
        target=_target_label(request.target),
        board_name=request.board_name,
        board_role=request.board_role,
        flash_method=request.flash_method,
        artifact_path=request.artifact_path,
        expected_uuid=request.expected_uuid,
        summary="Não foi possível executar preflight de flash.",
        findings=[],
        sections={"error": _trim(command_log or error, 3000)},
        parsed={},
        rollback=rollback_steps(request),
        error=error,
    )


def _blocked_execute(request: SetupFlashExecuteRequest, reasons: list[str], command_log: str) -> SetupFlashExecuteResponse:
    return SetupFlashExecuteResponse(
        safe_mode="flash_supervised_blocked",
        status="blocked",
        target=_target_label(request.target),
        board_name=request.board_name,
        board_role=request.board_role,
        flash_method=request.flash_method,
        artifact_path=request.artifact_path,
        expected_uuid=request.expected_uuid,
        summary="Flash supervisionado bloqueado.",
        command_log=command_log,
        rollback=rollback_steps(request),
        blocked_reasons=reasons,
    )


def _requires_recovery(
    request: SetupFlashExecuteRequest,
    reason: str,
    command_log: str,
    duration_ms: int,
) -> SetupFlashExecuteResponse:
    return SetupFlashExecuteResponse(
        safe_mode="flash_supervised_can_katapult",
        status="requires_recovery",
        target=_target_label(request.target),
        board_name=request.board_name,
        board_role=request.board_role,
        flash_method=request.flash_method,
        artifact_path=request.artifact_path,
        expected_uuid=request.expected_uuid,
        summary="Flash falhou ou ficou inconclusivo; seguir rollback manual.",
        command_log=command_log,
        duration_ms=duration_ms,
        rollback=rollback_steps(request),
        blocked_reasons=[reason],
    )


def _run_from_row(row) -> SetupFlashRunRecord:
    return SetupFlashRunRecord(
        id=int(row["id"]),
        run_type=row["run_type"],
        status=row["status"],
        safe_mode=row["safe_mode"],
        target_host=row["target_host"],
        target_port=int(row["target_port"]),
        target_user=row["target_user"],
        board_name=row["board_name"],
        board_role=row["board_role"],
        flash_method=row["flash_method"],
        can_interface=row["can_interface"],
        expected_uuid=row["expected_uuid"],
        artifact_path=row["artifact_path"],
        artifact_sha256=row["artifact_sha256"],
        previous_binary_path=row["previous_binary_path"],
        confirmation_phrase=row["confirmation_phrase"],
        duration_ms=row["duration_ms"],
        summary=json.loads(row["summary_json"]),
        preflight=json.loads(row["preflight_json"]) if row["preflight_json"] else None,
        plan=json.loads(row["plan_json"]) if row["plan_json"] else None,
        command_log=row["command_log"],
        rollback=json.loads(row["rollback_json"]),
        error_message=row["error_message"],
        created_at=row["created_at"],
    )
