from __future__ import annotations

import json
import re
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.auth import scoped_where_clause
from app.database import connect_database
from app.reports import Sanitizer
from app.setup_firmware import _line_value, _parse_output_sections, _trim
from app.setup_wizard import SetupSshTarget, _target_label


SetupFinalStatus = Literal[
    "approved_for_calibration",
    "approved_with_notes",
    "blocked",
    "needs_manual_intervention",
]
SetupFinalCheckStatus = Literal["ok", "warning", "blocked", "manual"]


class SetupFinalValidationRequest(BaseModel):
    target: SetupSshTarget
    interface_name: str = Field(default="can0", min_length=3, max_length=24)
    expected_uuids: list[str] = Field(default_factory=list, max_length=12)
    config_root: str = Field(default="~/printer_data/config", min_length=1, max_length=240)
    log_root: str = Field(default="~/printer_data/logs", min_length=1, max_length=240)

    @field_validator("interface_name")
    @classmethod
    def _validate_interface(cls, value: str) -> str:
        cleaned = value.strip()
        if not re.fullmatch(r"[a-zA-Z0-9_.:-]+", cleaned):
            raise ValueError("interface_name inválida")
        return cleaned

    @field_validator("expected_uuids")
    @classmethod
    def _validate_uuids(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        for item in value:
            candidate = item.strip().lower()
            if not candidate:
                continue
            if not re.fullmatch(r"[0-9a-f]{8,32}", candidate):
                raise ValueError("expected_uuids contém UUID inválido")
            if candidate not in cleaned:
                cleaned.append(candidate)
        return cleaned


class SetupFinalValidationCheck(BaseModel):
    key: str
    status: SetupFinalCheckStatus
    title: str
    detail: str
    action: str


class SetupFinalValidationResponse(BaseModel):
    safe_mode: str
    connected: bool
    status: SetupFinalStatus
    target: str
    interface_name: str
    expected_uuids: list[str]
    summary: str
    checks: list[SetupFinalValidationCheck]
    sections: dict[str, str]
    report_markdown: str
    history_id: int | None = None
    error: str | None = None


class SetupFinalValidationRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: SetupFinalStatus
    safe_mode: str
    target_host: str
    target_port: int
    target_user: str
    interface_name: str
    expected_uuids: list[str]
    summary: str
    checks: list[dict[str, object]]
    report_markdown: str
    error_message: str | None
    created_at: str


@dataclass(frozen=True)
class SetupFinalValidationRepository:
    database_path: Path
    user_id: int | None = None
    organization_ids: tuple[int, ...] = ()

    def create_run(self, request: SetupFinalValidationRequest, response: SetupFinalValidationResponse) -> int:
        target = request.target
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO setup_final_validation_runs (
                    status, safe_mode, target_host, target_port, target_user,
                    interface_name, expected_uuids_json, summary, checks_json,
                    sections_json, report_markdown, error_message, owner_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    response.status,
                    response.safe_mode,
                    target.host,
                    target.port,
                    target.username,
                    request.interface_name,
                    json.dumps(request.expected_uuids, ensure_ascii=False),
                    response.summary,
                    json.dumps([check.model_dump() for check in response.checks], ensure_ascii=False),
                    json.dumps(response.sections, ensure_ascii=False),
                    response.report_markdown,
                    response.error,
                    self.user_id,
                ),
            )
            return int(cursor.lastrowid)

    def list_runs(self, limit: int = 20) -> list[SetupFinalValidationRunRecord]:
        with connect_database(self.database_path) as connection:
            where_clause, params = _scope_sql("setup_final_validation_runs", self.user_id, self.organization_ids)
            rows = connection.execute(
                f"""
                SELECT id, status, safe_mode, target_host, target_port, target_user,
                       interface_name, expected_uuids_json, summary, checks_json,
                       report_markdown, error_message, created_at
                FROM setup_final_validation_runs
                {where_clause}
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (*params, limit),
            ).fetchall()
        return [_run_from_row(row) for row in rows]


async def run_setup_final_validation(request: SetupFinalValidationRequest) -> SetupFinalValidationResponse:
    result = await _run_remote_script(
        request.target,
        _remote_validation_script(request),
        timeout_seconds=max(request.target.timeout_seconds, 25.0),
    )
    if result["error"]:
        return _connection_error_response(request, str(result["error"]))
    output = f"{result['stdout']}\n{result['stderr']}"
    if int(result["exit_code"] or 0) != 0:
        return _connection_error_response(request, f"exit_code={result['exit_code']}", output)
    sections = {key: _trim(value, 5000) for key, value in _parse_output_sections(str(result["stdout"])).items()}
    checks = _build_checks(request, sections)
    status = _final_status(checks)
    summary = _summary(status, checks)
    report = _build_report(request, status, summary, checks, sections)
    sanitized_sections = _sanitize_sections(sections)
    return SetupFinalValidationResponse(
        safe_mode="final_validation_read_only",
        connected=True,
        status=status,
        target=_target_label(request.target),
        interface_name=request.interface_name,
        expected_uuids=request.expected_uuids,
        summary=summary,
        checks=checks,
        sections=sanitized_sections,
        report_markdown=report,
    )


def _remote_validation_script(request: SetupFinalValidationRequest) -> str:
    iface = shlex.quote(request.interface_name)
    config_root = shlex.quote(request.config_root)
    log_root = shlex.quote(request.log_root)
    return f"""set +e
IFACE={iface}
CONFIG_ROOT={config_root}
LOG_ROOT={log_root}
expand_path() {{
  case "$1" in
    "~") printf '%s\\n' "$HOME" ;;
    "~/"*) printf '%s/%s\\n' "$HOME" "${{1#~/}}" ;;
    *) printf '%s\\n' "$1" ;;
  esac
}}
CONFIG_ROOT="$(expand_path "$CONFIG_ROOT")"
LOG_ROOT="$(expand_path "$LOG_ROOT")"
printf 'SECTION tools\\n'
for tool in curl python3 systemctl ip grep tail find sed; do
  if command -v "$tool" >/dev/null 2>&1; then printf '%s=present:%s\\n' "$tool" "$(command -v "$tool")"; else printf '%s=missing\\n' "$tool"; fi
done
printf '\\nSECTION services\\n'
if command -v systemctl >/dev/null 2>&1; then
  for svc in klipper moonraker crowsnest mainsail nginx "$IFACE"; do
    systemctl is-active "$svc" 2>/dev/null | sed "s/^/$svc=/"
  done
else
  printf 'systemctl_unavailable\\n'
fi
printf '\\nSECTION server_info\\n'
curl -fsS 'http://127.0.0.1:7125/server/info' 2>/dev/null | head -c 2400 || printf 'server_info_unavailable\\n'
printf '\\nSECTION printer_info\\n'
curl -fsS 'http://127.0.0.1:7125/printer/info' 2>/dev/null | head -c 2400 || printf 'printer_info_unavailable\\n'
printf '\\nSECTION print_stats\\n'
curl -fsS 'http://127.0.0.1:7125/printer/objects/query?print_stats' 2>/dev/null | head -c 1600 || printf 'print_stats_unavailable\\n'
printf '\\nSECTION temperatures\\n'
curl -fsS 'http://127.0.0.1:7125/printer/objects/query?extruder=temperature,target&heater_bed=temperature,target' 2>/dev/null | head -c 1600 || printf 'temperatures_unavailable\\n'
printf '\\nSECTION update_status\\n'
curl -fsS 'http://127.0.0.1:7125/machine/update/status' 2>/dev/null | head -c 3000 || printf 'update_status_unavailable\\n'
printf '\\nSECTION can\\n'
ip -details -statistics link show "$IFACE" 2>&1 | head -c 2400
printf '\\nSECTION uuid_query\\n'
if [ -x "$HOME/klippy-env/bin/python" ] && [ -f "$HOME/klipper/scripts/canbus_query.py" ]; then
  timeout 8 "$HOME/klippy-env/bin/python" "$HOME/klipper/scripts/canbus_query.py" "$IFACE" 2>&1
else
  printf 'canbus_query_unavailable\\n'
fi
printf '\\nSECTION config_summary\\n'
if [ -d "$CONFIG_ROOT" ]; then
  printf 'config_root_exists=yes\\n'
  find "$CONFIG_ROOT" -maxdepth 2 -type f \\( -name '*.cfg' -o -name 'printer.cfg' \\) | sed 's#^#cfg=#' | head -n 80
  grep -RHE '^[[:space:]]*\\[mcu|^[[:space:]]*serial:|^[[:space:]]*canbus_uuid:|^[[:space:]]*\\[include' "$CONFIG_ROOT" 2>/dev/null | head -n 120
else
  printf 'config_root_exists=no\\n'
fi
printf '\\nSECTION recent_errors\\n'
for log in "$LOG_ROOT/klippy.log" "$LOG_ROOT/moonraker.log"; do
  if [ -f "$log" ]; then
    printf 'log=%s\\n' "$log"
    tail -n 1000 "$log" | grep -aEi 'error|traceback|exception|shutdown|disconnect|timeout|mcu.*lost|bytes_invalid|timer too close' | tail -n 40
  else
    printf 'missing_log=%s\\n' "$log"
  fi
done
"""


def _build_checks(
    request: SetupFinalValidationRequest,
    sections: dict[str, str],
) -> list[SetupFinalValidationCheck]:
    return [
        _service_check(sections.get("services", "")),
        _moonraker_check(sections.get("server_info", "")),
        _klipper_check(sections.get("printer_info", "")),
        _print_state_check(sections.get("print_stats", "")),
        _temperature_check(sections.get("temperatures", "")),
        _can_check(request.interface_name, sections.get("can", "")),
        _uuid_check(request.expected_uuids, sections.get("uuid_query", ""), sections.get("config_summary", "")),
        _config_check(sections.get("config_summary", "")),
        _log_check(sections.get("recent_errors", "")),
        _update_check(sections.get("update_status", "")),
    ]


def _service_check(services: str) -> SetupFinalValidationCheck:
    missing = [name for name in ("klipper", "moonraker") if f"{name}=active" not in services]
    return SetupFinalValidationCheck(
        key="services",
        status="blocked" if missing else "ok",
        title="Serviços base",
        detail=f"Serviços críticos inativos: {', '.join(missing)}." if missing else "Klipper e Moonraker ativos.",
        action="Subir serviços base antes de liberar calibração." if missing else "Sem ação.",
    )


def _moonraker_check(server_info: str) -> SetupFinalValidationCheck:
    unavailable = "server_info_unavailable" in server_info or not server_info.strip()
    return SetupFinalValidationCheck(
        key="moonraker",
        status="blocked" if unavailable else "ok",
        title="Moonraker",
        detail="Moonraker local não respondeu." if unavailable else "Moonraker respondeu em leitura local.",
        action="Validar serviço Moonraker e rede local." if unavailable else "Sem ação.",
    )


def _klipper_check(printer_info: str) -> SetupFinalValidationCheck:
    unavailable = "printer_info_unavailable" in printer_info or not printer_info.strip()
    lower = printer_info.lower()
    ready = '"state":"ready"' in lower or '"state": "ready"' in lower
    shutdown = "shutdown" in lower or "error" in lower
    status: SetupFinalCheckStatus = "blocked" if unavailable or shutdown else "ok" if ready else "warning"
    return SetupFinalValidationCheck(
        key="klipper",
        status=status,
        title="Klipper",
        detail="Klipper não respondeu ou reportou erro." if status == "blocked" else "Klipper pronto." if ready else "Klipper respondeu, mas não confirmou estado ready.",
        action="Corrigir erro do Klipper antes de calibrar." if status == "blocked" else "Revisar estado antes da primeira calibração." if status == "warning" else "Sem ação.",
    )


def _print_state_check(print_stats: str) -> SetupFinalValidationCheck:
    lower = print_stats.lower()
    busy = '"state":"printing"' in lower or '"state": "printing"' in lower or '"state":"paused"' in lower or '"state": "paused"' in lower
    return SetupFinalValidationCheck(
        key="print_state",
        status="blocked" if busy else "ok",
        title="Impressão parada",
        detail="Há impressão em andamento ou pausada." if busy else "Nenhuma impressão ativa detectada.",
        action="Aguardar/cancelar impressão antes de validar aceite." if busy else "Sem ação.",
    )


def _temperature_check(temperatures: str) -> SetupFinalValidationCheck:
    unavailable = "temperatures_unavailable" in temperatures
    active_target = re.search(r'"target"\s*:\s*(?!0(?:\.0)?[,}])([1-9][0-9.]*)', temperatures)
    return SetupFinalValidationCheck(
        key="temperatures",
        status="manual" if unavailable else "warning" if active_target else "ok",
        title="Temperaturas",
        detail="Temperaturas indisponíveis." if unavailable else "Há alvo de aquecimento ativo." if active_target else "Sem aquecimento comandado.",
        action="Conferir manualmente sensores." if unavailable else "Zerar alvos antes de manutenção/calibração." if active_target else "Sem ação.",
    )


def _can_check(interface_name: str, can: str) -> SetupFinalValidationCheck:
    down = "does not exist" in can.lower() or "state DOWN" in can or not can.strip()
    return SetupFinalValidationCheck(
        key="can",
        status="blocked" if down else "ok",
        title="Barramento CAN",
        detail=f"Interface {interface_name} indisponível." if down else f"Interface {interface_name} respondeu.",
        action="Corrigir CAN antes de validar MCUs." if down else "Sem ação.",
    )


def _uuid_check(expected_uuids: list[str], uuid_query: str, config_summary: str) -> SetupFinalValidationCheck:
    found = {uuid.lower() for uuid in re.findall(r"canbus_uuid=([0-9a-fA-F]+)|canbus_uuid:\s*([0-9a-fA-F]+)", f"{uuid_query}\n{config_summary}") for uuid in uuid if uuid}
    missing = [uuid for uuid in expected_uuids if uuid not in found]
    if not expected_uuids:
        return SetupFinalValidationCheck(
            key="uuids",
            status="manual",
            title="UUIDs de MCU",
            detail="Nenhum UUID esperado informado para comparação.",
            action="Informar UUIDs esperados para fechar aceite eletrônico.",
        )
    return SetupFinalValidationCheck(
        key="uuids",
        status="blocked" if missing else "ok",
        title="UUIDs de MCU",
        detail=f"UUIDs não confirmados: {', '.join(missing)}." if missing else "UUIDs esperados encontrados em CAN/config.",
        action="Revisar bootloader, CAN ou printer.cfg." if missing else "Sem ação.",
    )


def _config_check(config_summary: str) -> SetupFinalValidationCheck:
    missing_root = "config_root_exists=no" in config_summary
    has_mcu = "[mcu" in config_summary.lower()
    has_identifier = "serial:" in config_summary.lower() or "canbus_uuid:" in config_summary.lower()
    blocked = missing_root or not has_mcu or not has_identifier
    return SetupFinalValidationCheck(
        key="config",
        status="blocked" if blocked else "ok",
        title="Configuração mínima",
        detail="Configuração mínima de MCU não encontrada." if blocked else "Configuração contém MCU e identificador serial/CAN.",
        action="Criar/revisar printer.cfg e includes antes de calibrar." if blocked else "Sem ação.",
    )


def _log_check(recent_errors: str) -> SetupFinalValidationCheck:
    severe = any(token in recent_errors.lower() for token in ("traceback", "shutdown", "mcu '", "timer too close"))
    warning = any(token in recent_errors.lower() for token in ("error", "exception", "disconnect", "timeout", "bytes_invalid"))
    return SetupFinalValidationCheck(
        key="logs",
        status="blocked" if severe else "warning" if warning else "ok",
        title="Erros recentes",
        detail="Erro crítico recente em logs." if severe else "Avisos/erros recentes encontrados." if warning else "Sem erro crítico recente nos trechos lidos.",
        action="Revisar logs antes de calibrar." if severe or warning else "Sem ação.",
    )


def _update_check(update_status: str) -> SetupFinalValidationCheck:
    unavailable = "update_status_unavailable" in update_status
    dirty = "dirty" in update_status.lower()
    return SetupFinalValidationCheck(
        key="updates",
        status="manual" if unavailable else "warning" if dirty else "ok",
        title="Update Manager",
        detail="Update Manager indisponível." if unavailable else "Há componente com estado dirty." if dirty else "Update Manager respondeu sem alerta crítico simples.",
        action="Revisar Moonraker Update Manager depois do aceite base." if unavailable or dirty else "Sem ação.",
    )


def _final_status(checks: list[SetupFinalValidationCheck]) -> SetupFinalStatus:
    if any(check.status == "blocked" for check in checks):
        return "blocked"
    if any(check.status == "manual" for check in checks):
        return "needs_manual_intervention"
    if any(check.status == "warning" for check in checks):
        return "approved_with_notes"
    return "approved_for_calibration"


def _summary(status: SetupFinalStatus, checks: list[SetupFinalValidationCheck]) -> str:
    blocked = sum(1 for check in checks if check.status == "blocked")
    warnings = sum(1 for check in checks if check.status == "warning")
    manual = sum(1 for check in checks if check.status == "manual")
    if status == "approved_for_calibration":
        return "Base eletrônica e software aprovados para iniciar calibração."
    if status == "approved_with_notes":
        return f"Base aprovada com {warnings} observação(ões) antes da calibração."
    if status == "needs_manual_intervention":
        return f"Validação requer {manual} conferência(s) manual(is)."
    return f"Validação bloqueada por {blocked} item(ns)."


def _build_report(
    request: SetupFinalValidationRequest,
    status: SetupFinalStatus,
    summary: str,
    checks: list[SetupFinalValidationCheck],
    sections: dict[str, str],
) -> str:
    sanitizer = Sanitizer()
    lines = [
        "# Aceite técnico da base Klipper",
        "",
        f"- Alvo: {sanitizer.clean(_target_label(request.target))}",
        f"- Interface CAN: {sanitizer.clean(request.interface_name)}",
        f"- Status: {status}",
        f"- Resumo: {sanitizer.clean(summary)}",
        f"- UUIDs esperados: {sanitizer.clean(', '.join(request.expected_uuids) or 'não informado')}",
        "",
        "## Checks",
    ]
    for check in checks:
        lines.append(f"- {check.status}: {sanitizer.clean(check.title)} - {sanitizer.clean(check.detail)} Ação: {sanitizer.clean(check.action)}")
    lines.extend(["", "## Evidências Sanitizadas"])
    for key in ("services", "printer_info", "server_info", "can", "config_summary", "recent_errors"):
        value = sanitizer.clean(sections.get(key, "")[:1600] or "-")
        lines.extend([f"### {key}", "```text", value, "```"])
    lines.extend(["", f"Redações aplicadas: {', '.join(sorted(sanitizer.redactions)) or 'nenhuma'}"])
    return "\n".join(lines)


def _sanitize_sections(sections: dict[str, str]) -> dict[str, str]:
    sanitizer = Sanitizer()
    return {key: sanitizer.clean(value) for key, value in sections.items()}


async def _run_remote_script(target: SetupSshTarget, script: str, timeout_seconds: float) -> dict[str, object]:
    from app.agent_host import run_host_script_via_agent

    return await run_host_script_via_agent(
        target,
        script,
        timeout_seconds=timeout_seconds,
        kind="setup_final_validation",
    )

def _connection_error_response(
    request: SetupFinalValidationRequest,
    error: str,
    command_log: str = "",
) -> SetupFinalValidationResponse:
    report = _build_report(request, "blocked", "Não foi possível executar validação final.", [], {"error": command_log or error})
    sanitized_error = Sanitizer().clean(command_log or error)
    return SetupFinalValidationResponse(
        safe_mode="final_validation_read_only",
        connected=False,
        status="blocked",
        target=_target_label(request.target),
        interface_name=request.interface_name,
        expected_uuids=request.expected_uuids,
        summary="Não foi possível executar validação final.",
        checks=[],
        sections={"error": _trim(sanitized_error, 3000)},
        report_markdown=report,
        error=error,
    )


def _run_from_row(row) -> SetupFinalValidationRunRecord:
    return SetupFinalValidationRunRecord(
        id=int(row["id"]),
        status=row["status"],
        safe_mode=row["safe_mode"],
        target_host=row["target_host"],
        target_port=int(row["target_port"]),
        target_user=row["target_user"],
        interface_name=row["interface_name"],
        expected_uuids=json.loads(row["expected_uuids_json"]),
        summary=row["summary"],
        checks=json.loads(row["checks_json"]),
        report_markdown=row["report_markdown"],
        error_message=row["error_message"],
        created_at=row["created_at"],
    )


def _scope_sql(table_alias: str, user_id: int | None, organization_ids: tuple[int, ...]) -> tuple[str, tuple[object, ...]]:
    if user_id is None:
        return "", ()
    return scoped_where_clause(table_alias, user_id, organization_ids)
