from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.auth import scoped_where_clause
from app.database import connect_database
from app.firmware.config_generator import generate_firmware_config_preview
from app.firmware.presets import BOARD_PRESETS
from app.setup_wizard import SetupCommandPlan, SetupSshTarget, _target_label


FIRMWARE_REMOTE_BUILD_CONFIRMATION = "BUILD_FIRMWARE_NO_FLASH"
FIRMWARE_REMOTE_BUILD_MODE_ENV = "PRINTORA_REMOTE_FIRMWARE_BUILD_MODE"
SetupFirmwareStatus = Literal["ok", "warning", "error", "blocked"]
SetupFirmwareRole = Literal["mainboard", "toolhead", "can_adapter", "unknown"]


class SetupFirmwareRequest(BaseModel):
    target: SetupSshTarget
    preset_id: str = Field(min_length=1, max_length=120)
    board_name: str = Field(min_length=1, max_length=120)
    board_role: SetupFirmwareRole = "unknown"
    can_interface: str = Field(default="can0", min_length=3, max_length=24)
    klipper_path: str = Field(default="~/klipper", min_length=1, max_length=220)
    output_root: str = Field(default="~/.local/share/printora/firmware-setup", min_length=1, max_length=260)
    variant_confirmed: bool = False

    @field_validator("can_interface")
    @classmethod
    def _validate_interface(cls, value: str) -> str:
        cleaned = value.strip()
        if not re.fullmatch(r"[a-zA-Z0-9_.:-]+", cleaned):
            raise ValueError("can_interface inválida")
        return cleaned


class SetupFirmwareBuildRequest(SetupFirmwareRequest):
    confirmation: str = Field(min_length=1, max_length=80)


class SetupFirmwarePlanStep(BaseModel):
    key: str
    title: str
    status: Literal["ready", "missing", "manual", "blocked"]
    detail: str
    commands: list[SetupCommandPlan] = Field(default_factory=list)
    rollback: str | None = None


class SetupFirmwarePlanResponse(BaseModel):
    safe_mode: str
    status: SetupFirmwareStatus
    target: str
    preset_id: str
    board_name: str
    board_role: SetupFirmwareRole
    summary: str
    config_preview: str
    config_sha256: str
    artifact_dir: str
    expected_binary_path: str
    steps: list[SetupFirmwarePlanStep]
    blocked_reasons: list[str]
    history_id: int | None = None


class SetupFirmwareBuildResponse(BaseModel):
    safe_mode: str
    status: SetupFirmwareStatus
    target: str
    preset_id: str
    board_name: str
    board_role: SetupFirmwareRole
    summary: str
    artifact_dir: str | None = None
    config_path: str | None = None
    binary_path: str | None = None
    config_sha256: str | None = None
    binary_sha256: str | None = None
    uuid_query: list[str] = Field(default_factory=list)
    command_log: str = ""
    blocked_reasons: list[str] = Field(default_factory=list)
    history_id: int | None = None


class SetupFirmwareRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_type: Literal["plan", "build"]
    status: SetupFirmwareStatus
    safe_mode: str
    target_host: str
    target_port: int
    target_user: str
    board_name: str
    board_role: SetupFirmwareRole
    preset_id: str
    can_interface: str
    config_path: str | None
    artifact_dir: str | None
    binary_path: str | None
    config_sha256: str | None
    binary_sha256: str | None
    uuid_query: list[str]
    summary: dict[str, object]
    plan: dict[str, object] | None
    command_log: str | None
    error_message: str | None
    created_at: str


@dataclass(frozen=True)
class SetupFirmwareRunRepository:
    database_path: Path
    user_id: int | None = None
    organization_ids: tuple[int, ...] = ()

    def create_plan(self, request: SetupFirmwareRequest, response: SetupFirmwarePlanResponse) -> int:
        return self._create_run(
            run_type="plan",
            request=request,
            status=response.status,
            safe_mode=response.safe_mode,
            config_path=None,
            artifact_dir=response.artifact_dir,
            binary_path=response.expected_binary_path,
            config_sha256=response.config_sha256,
            binary_sha256=None,
            uuid_query=[],
            summary={"summary": response.summary, "blocked_reasons": response.blocked_reasons},
            plan={"steps": [step.model_dump() for step in response.steps]},
            command_log=None,
            error="; ".join(response.blocked_reasons) if response.blocked_reasons else None,
        )

    def create_build(self, request: SetupFirmwareRequest, response: SetupFirmwareBuildResponse) -> int:
        return self._create_run(
            run_type="build",
            request=request,
            status=response.status,
            safe_mode=response.safe_mode,
            config_path=response.config_path,
            artifact_dir=response.artifact_dir,
            binary_path=response.binary_path,
            config_sha256=response.config_sha256,
            binary_sha256=response.binary_sha256,
            uuid_query=response.uuid_query,
            summary={"summary": response.summary, "blocked_reasons": response.blocked_reasons},
            plan=None,
            command_log=response.command_log,
            error="; ".join(response.blocked_reasons) if response.blocked_reasons else None,
        )

    def list_runs(self, limit: int = 20) -> list[SetupFirmwareRunRecord]:
        with connect_database(self.database_path) as connection:
            where_clause, params = _scope_sql("setup_firmware_runs", self.user_id, self.organization_ids)
            rows = connection.execute(
                f"""
                SELECT id, run_type, status, safe_mode, target_host, target_port, target_user,
                       board_name, board_role, preset_id, can_interface, config_path, artifact_dir,
                       binary_path, config_sha256, binary_sha256, uuid_query_json, summary_json,
                       plan_json, command_log, error_message, created_at
                FROM setup_firmware_runs
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()
        return [_run_from_row(row) for row in rows]

    def _create_run(
        self,
        *,
        run_type: Literal["plan", "build"],
        request: SetupFirmwareRequest,
        status: SetupFirmwareStatus,
        safe_mode: str,
        config_path: str | None,
        artifact_dir: str | None,
        binary_path: str | None,
        config_sha256: str | None,
        binary_sha256: str | None,
        uuid_query: list[str],
        summary: dict[str, object],
        plan: dict[str, object] | None,
        command_log: str | None,
        error: str | None,
    ) -> int:
        target = request.target
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO setup_firmware_runs (
                    run_type, status, safe_mode, target_host, target_port, target_user,
                    board_name, board_role, preset_id, can_interface, config_path, artifact_dir,
                    binary_path, config_sha256, binary_sha256, uuid_query_json, summary_json,
                    plan_json, command_log, error_message, owner_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    request.preset_id,
                    request.can_interface,
                    config_path,
                    artifact_dir,
                    binary_path,
                    config_sha256,
                    binary_sha256,
                    json.dumps(uuid_query, ensure_ascii=False),
                    json.dumps(summary, ensure_ascii=False),
                    json.dumps(plan, ensure_ascii=False) if plan is not None else None,
                    command_log,
                    error,
                    self.user_id,
                ),
            )
            return int(cursor.lastrowid)


def build_setup_firmware_plan(request: SetupFirmwareRequest) -> SetupFirmwarePlanResponse:
    preset = _preset(request.preset_id)
    preview = generate_firmware_config_preview(preset)
    config_sha = hashlib.sha256(preview.content.encode()).hexdigest()
    artifact_dir = f"{request.output_root.rstrip('/')}/{_slug(request.board_name)}"
    expected_binary = f"{artifact_dir}/{Path(preset.build_output).name}"
    blocked_reasons: list[str] = []
    if not request.variant_confirmed:
        blocked_reasons.append("Variante física ainda não confirmada.")
    if preset.build_config_status != "complete":
        blocked_reasons.append(f"Preset incompleto para build: {preset.build_config_status}.")
    steps = [
        SetupFirmwarePlanStep(
            key="confirm_variant",
            title="Confirmar hardware físico",
            status="ready" if request.variant_confirmed else "blocked",
            detail=f"{request.board_name} usando preset {preset.id}: MCU {preset.mcu}, conexão {preset.connection_type}, output {preset.build_output}.",
            commands=[],
        ),
        SetupFirmwarePlanStep(
            key="generate_config",
            title="Gerar .config remoto",
            status="ready" if request.variant_confirmed else "blocked",
            detail=f".config determinístico com sha256 {config_sha[:12]} será salvo em {artifact_dir}/generated/{Path(preset.config_file).name}.",
            commands=[
                SetupCommandPlan(command=f"PLAN mkdir -p {artifact_dir}/generated {artifact_dir}/logs", risk="mutable", reason="Cria diretório controlado de artefatos Printora."),
                SetupCommandPlan(command=f"PLAN escrever {artifact_dir}/generated/{Path(preset.config_file).name}", risk="mutable", reason="Salva .config gerado sem tocar printer.cfg."),
            ],
            rollback=f"Remover diretório de artefatos {artifact_dir} se o build for descartado.",
        ),
        SetupFirmwarePlanStep(
            key="remote_build",
            title="Build remoto sem flash",
            status="ready" if request.variant_confirmed else "blocked",
            detail=f"Build em {request.klipper_path}; backup/restauração de .config e cópia de {preset.build_output} para {expected_binary}.",
            commands=[
                SetupCommandPlan(command=f"PLAN cp {request.klipper_path.rstrip('/')}/.config {artifact_dir}/.config.before-build", risk="mutable", reason="Preserva .config atual do Klipper."),
                SetupCommandPlan(command=f"PLAN cp generated config {request.klipper_path.rstrip('/')}/.config", risk="mutable", reason="Usa config gerado somente durante o build."),
                SetupCommandPlan(command=f"PLAN cd {request.klipper_path.rstrip('/')} && make clean && make", risk="mutable", reason="Compila firmware sem flash."),
                SetupCommandPlan(command=f"PLAN cp {request.klipper_path.rstrip('/')}/{preset.build_output} {expected_binary}", risk="mutable", reason="Copia binário para artefatos Printora."),
                SetupCommandPlan(command=f"PLAN restaurar {request.klipper_path.rstrip('/')}/.config", risk="mutable", reason="Restaura configuração anterior em sucesso ou falha."),
            ],
            rollback=f"Restaurar {artifact_dir}/.config.before-build em {request.klipper_path.rstrip('/')}/.config.",
        ),
        SetupFirmwarePlanStep(
            key="uuid_query",
            title="Capturar UUIDs CAN",
            status="manual",
            detail=f"Consultar UUIDs em {request.can_interface} quando Klipper tooling existir; resultado é sugestão, não alteração de config.",
            commands=[
                SetupCommandPlan(command=f"PLAN ~/klippy-env/bin/python ~/klipper/scripts/canbus_query.py {request.can_interface}", risk="read_only", reason="Captura UUIDs CAN após build."),
            ],
        ),
    ]
    status: SetupFirmwareStatus = "blocked" if blocked_reasons else "ok"
    return SetupFirmwarePlanResponse(
        safe_mode="firmware_remote_dry_run_plan",
        status=status,
        target=_target_label(request.target),
        preset_id=preset.id,
        board_name=request.board_name,
        board_role=request.board_role,
        summary="Plano de firmware remoto bloqueado." if blocked_reasons else "Plano de firmware remoto pronto.",
        config_preview=preview.content,
        config_sha256=config_sha,
        artifact_dir=artifact_dir,
        expected_binary_path=expected_binary,
        steps=steps,
        blocked_reasons=blocked_reasons,
    )


async def execute_setup_firmware_build(request: SetupFirmwareBuildRequest) -> SetupFirmwareBuildResponse:
    if request.confirmation != FIRMWARE_REMOTE_BUILD_CONFIRMATION:
        return _blocked_build(request, ["Confirmação textual inválida."], "")
    if os.getenv(FIRMWARE_REMOTE_BUILD_MODE_ENV) != "remote":
        return _blocked_build(request, [f"{FIRMWARE_REMOTE_BUILD_MODE_ENV}=remote não está habilitado."], "")
    plan = build_setup_firmware_plan(request)
    if plan.blocked_reasons:
        return _blocked_build(request, plan.blocked_reasons, "")
    preset = _preset(request.preset_id)
    preview = generate_firmware_config_preview(preset)
    script = _remote_build_script(request, preset.build_output, preview.content)
    result = await _run_remote_script(request.target, script, timeout_seconds=max(request.target.timeout_seconds, 120.0))
    command_log = _trim(f"{result['stdout']}\n{result['stderr']}", 10000)
    if result["error"]:
        return _error_build(request, str(result["error"]), command_log)
    if int(result["exit_code"] or 0) != 0:
        return _error_build(request, f"exit_code={result['exit_code']}", command_log)
    sections = _parse_output_sections(str(result["stdout"]))
    uuid_query = re.findall(r"canbus_uuid=([0-9a-fA-F]+)", sections.get("uuid_query", ""))
    return SetupFirmwareBuildResponse(
        safe_mode="firmware_remote_build_no_flash",
        status="ok",
        target=_target_label(request.target),
        preset_id=request.preset_id,
        board_name=request.board_name,
        board_role=request.board_role,
        summary="Build remoto concluído sem flash.",
        artifact_dir=_line_value(sections.get("artifact", ""), "artifact_dir"),
        config_path=_line_value(sections.get("artifact", ""), "generated_config"),
        binary_path=_line_value(sections.get("artifact", ""), "binary_path"),
        config_sha256=_line_value(sections.get("hashes", ""), "config_sha256"),
        binary_sha256=_line_value(sections.get("hashes", ""), "binary_sha256"),
        uuid_query=uuid_query,
        command_log=command_log,
    )


def _remote_build_script(request: SetupFirmwareBuildRequest, build_output: str, config_content: str) -> str:
    config_b64 = base64.b64encode(config_content.encode()).decode()
    klipper = request.klipper_path.rstrip("/")
    output_root = request.output_root.rstrip("/")
    board_slug = _slug(request.board_name)
    config_name = Path(_preset(request.preset_id).config_file).name
    binary_name = Path(build_output).name
    return f"""set -euo pipefail
KLIPPER_PATH={shlex.quote(klipper)}
OUTPUT_ROOT={shlex.quote(output_root)}
BOARD_SLUG={shlex.quote(board_slug)}
CAN_IFACE={shlex.quote(request.can_interface)}
BUILD_OUTPUT={shlex.quote(build_output)}
ARTIFACT_DIR="$OUTPUT_ROOT/$BOARD_SLUG"
GENERATED_DIR="$ARTIFACT_DIR/generated"
LOG_DIR="$ARTIFACT_DIR/logs"
GENERATED_CONFIG="$GENERATED_DIR/{config_name}"
BINARY_PATH="$ARTIFACT_DIR/{binary_name}"
BACKUP_CONFIG="$ARTIFACT_DIR/.config.before-build"
RESTORE_NEEDED=0
restore_config() {{
  if [ "$RESTORE_NEEDED" = "1" ] && [ -f "$BACKUP_CONFIG" ]; then
    cp "$BACKUP_CONFIG" "$KLIPPER_PATH/.config"
  fi
}}
trap restore_config EXIT
printf 'SECTION preflight\\n'
test -d "$KLIPPER_PATH"
test -f "$KLIPPER_PATH/Makefile"
test -f "$KLIPPER_PATH/.config"
command -v make >/dev/null
mkdir -p "$GENERATED_DIR" "$LOG_DIR"
printf 'SECTION artifact\\n'
printf 'artifact_dir=%s\\n' "$ARTIFACT_DIR"
printf 'generated_config=%s\\n' "$GENERATED_CONFIG"
printf 'binary_path=%s\\n' "$BINARY_PATH"
printf '{config_b64}' | base64 -d > "$GENERATED_CONFIG"
cp "$KLIPPER_PATH/.config" "$BACKUP_CONFIG"
RESTORE_NEEDED=1
cp "$GENERATED_CONFIG" "$KLIPPER_PATH/.config"
printf '\\nSECTION build\\n'
( cd "$KLIPPER_PATH" && make clean && make ) > "$LOG_DIR/build.log" 2>&1
tail -n 120 "$LOG_DIR/build.log"
test -f "$KLIPPER_PATH/$BUILD_OUTPUT"
cp "$KLIPPER_PATH/$BUILD_OUTPUT" "$BINARY_PATH"
restore_config
RESTORE_NEEDED=0
printf '\\nSECTION hashes\\n'
printf 'config_sha256=%s\\n' "$(sha256sum "$GENERATED_CONFIG" | awk '{{print $1}}')"
printf 'binary_sha256=%s\\n' "$(sha256sum "$BINARY_PATH" | awk '{{print $1}}')"
printf '\\nSECTION uuid_query\\n'
if [ -x "$HOME/klippy-env/bin/python" ] && [ -f "$HOME/klipper/scripts/canbus_query.py" ]; then
  timeout 8 "$HOME/klippy-env/bin/python" "$HOME/klipper/scripts/canbus_query.py" "$CAN_IFACE" 2>&1 || true
else
  printf 'canbus_query_unavailable\\n'
fi
"""


async def _run_remote_script(target: SetupSshTarget, script: str, timeout_seconds: float) -> dict[str, object]:
    from app.agent_host import run_host_script_via_agent

    return await run_host_script_via_agent(
        target,
        script,
        timeout_seconds=timeout_seconds,
        kind="setup_firmware",
    )

def _blocked_build(request: SetupFirmwareBuildRequest, reasons: list[str], command_log: str) -> SetupFirmwareBuildResponse:
    return SetupFirmwareBuildResponse(
        safe_mode="firmware_remote_build_blocked",
        status="blocked",
        target=_target_label(request.target),
        preset_id=request.preset_id,
        board_name=request.board_name,
        board_role=request.board_role,
        summary="Build remoto de firmware bloqueado.",
        command_log=command_log,
        blocked_reasons=reasons,
    )


def _error_build(request: SetupFirmwareBuildRequest, reason: str, command_log: str) -> SetupFirmwareBuildResponse:
    return SetupFirmwareBuildResponse(
        safe_mode="firmware_remote_build_no_flash",
        status="error",
        target=_target_label(request.target),
        preset_id=request.preset_id,
        board_name=request.board_name,
        board_role=request.board_role,
        summary="Build remoto de firmware falhou sem executar flash.",
        command_log=command_log,
        blocked_reasons=[reason],
    )


def _run_from_row(row) -> SetupFirmwareRunRecord:
    return SetupFirmwareRunRecord(
        id=int(row["id"]),
        run_type=row["run_type"],
        status=row["status"],
        safe_mode=row["safe_mode"],
        target_host=row["target_host"],
        target_port=int(row["target_port"]),
        target_user=row["target_user"],
        board_name=row["board_name"],
        board_role=row["board_role"],
        preset_id=row["preset_id"],
        can_interface=row["can_interface"],
        config_path=row["config_path"],
        artifact_dir=row["artifact_dir"],
        binary_path=row["binary_path"],
        config_sha256=row["config_sha256"],
        binary_sha256=row["binary_sha256"],
        uuid_query=json.loads(row["uuid_query_json"]) if row["uuid_query_json"] else [],
        summary=json.loads(row["summary_json"]),
        plan=json.loads(row["plan_json"]) if row["plan_json"] else None,
        command_log=row["command_log"],
        error_message=row["error_message"],
        created_at=row["created_at"],
    )


def _scope_sql(table_alias: str, user_id: int | None, organization_ids: tuple[int, ...]) -> tuple[str, tuple[object, ...]]:
    if user_id is None:
        return "", ()
    return scoped_where_clause(table_alias, user_id, organization_ids)


def _preset(preset_id: str):
    preset = BOARD_PRESETS.get(preset_id)
    if preset is None:
        raise ValueError(f"Preset não encontrado: {preset_id}")
    return preset


def _slug(value: str) -> str:
    lowered = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "firmware-board"


def _trim(value: str, limit: int = 3000) -> str:
    cleaned = value.strip()
    return cleaned if len(cleaned) <= limit else f"{cleaned[:limit]}\n... truncado ..."


def _parse_output_sections(output: str) -> dict[str, str]:
    sections: dict[str, list[str]] = {}
    current = "preamble"
    sections[current] = []
    for line in output.splitlines():
        if line.startswith("SECTION "):
            current = line.removeprefix("SECTION ").strip()
            sections[current] = []
            continue
        sections.setdefault(current, []).append(line)
    return {key: "\n".join(lines).strip() for key, lines in sections.items()}


def _line_value(section: str, key: str) -> str | None:
    for line in section.splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip()
    return None
