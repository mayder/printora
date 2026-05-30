from __future__ import annotations

import asyncio
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.database import connect_database
from app.setup_wizard import SetupCommandPlan, SetupSshTarget, _target_label, split_sections


CAN_SETUP_CONFIRMATION = "CONFIGURAR CAN0"
CAN_SETUP_MODE_ENV = "PRINTORA_CAN_SETUP_MODE"
SetupCanStatus = Literal["ok", "warning", "error", "blocked"]


READ_ONLY_CAN_SCRIPT = r"""
set +e
IFACE="${PRINTORA_CAN_INTERFACE:-can0}"
BITRATE="${PRINTORA_CAN_BITRATE:-1000000}"
printf 'SECTION tools\n'
for tool in ip lsusb systemctl sudo modprobe lsmod curl python3; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '%s=present:%s\n' "$tool" "$(command -v "$tool")"
  else
    printf '%s=missing\n' "$tool"
  fi
done
printf '\nSECTION sudo\n'
sudo -n true >/dev/null 2>&1 && printf 'sudo_nopasswd=yes\n' || printf 'sudo_nopasswd=no\n'
printf '\nSECTION modules\n'
if command -v lsmod >/dev/null 2>&1; then lsmod 2>&1 | egrep -i '(^can|can_raw|can_dev|gs_usb)' || true; else printf 'lsmod_unavailable\n'; fi
printf '\nSECTION usb\n'
if command -v lsusb >/dev/null 2>&1; then lsusb 2>&1 | egrep -i 'can|u2c|stm|dfu|bigtreetech|katapult|klipper|gs_usb' || true; else printf 'lsusb_unavailable\n'; fi
printf '\nSECTION links\n'
if command -v ip >/dev/null 2>&1; then ip -brief link 2>&1; else printf 'ip_unavailable\n'; fi
printf '\nSECTION can\n'
if command -v ip >/dev/null 2>&1; then ip -details -statistics link show "$IFACE" 2>&1; else printf 'ip_unavailable\n'; fi
printf '\nSECTION config_files\n'
for f in "/etc/systemd/system/${IFACE}.service" "/etc/network/interfaces.d/${IFACE}" "/etc/systemd/network/25-${IFACE}.network"; do
  if [ -e "$f" ]; then printf 'present %s\n' "$f"; else printf 'missing %s\n' "$f"; fi
done
printf '\nSECTION services\n'
if command -v systemctl >/dev/null 2>&1; then
  systemctl list-units --type=service --all --no-pager 2>&1 | egrep -i "${IFACE}|klipper|moonraker" || true
else
  printf 'systemctl_unavailable\n'
fi
printf '\nSECTION print_state\n'
if command -v curl >/dev/null 2>&1; then
  curl -fsS 'http://127.0.0.1:7125/printer/objects/query?print_stats' 2>&1 | head -c 1200
else
  printf 'curl_unavailable\n'
fi
printf '\nSECTION uuid_query\n'
if [ -x "$HOME/klippy-env/bin/python" ] && [ -f "$HOME/klipper/scripts/canbus_query.py" ]; then
  timeout 8 "$HOME/klippy-env/bin/python" "$HOME/klipper/scripts/canbus_query.py" "$IFACE" 2>&1
else
  printf 'canbus_query_unavailable\n'
fi
"""


APPLY_CAN_SCRIPT = r"""
set -euo pipefail
IFACE="${PRINTORA_CAN_INTERFACE:-can0}"
BITRATE="${PRINTORA_CAN_BITRATE:-1000000}"
BACKUP_ROOT="$HOME/.local/share/printora/can-setup/backups"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="$BACKUP_ROOT/$STAMP"
SERVICE_PATH="/etc/systemd/system/${IFACE}.service"

printf 'SECTION preflight\n'
sudo -n true >/dev/null
if command -v curl >/dev/null 2>&1 && command -v python3 >/dev/null 2>&1; then
  STATE="$(curl -fsS 'http://127.0.0.1:7125/printer/objects/query?print_stats' 2>/dev/null | python3 -c 'import json,sys; data=json.load(sys.stdin); print(data.get("result",{}).get("status",{}).get("print_stats",{}).get("state","unknown"))' 2>/dev/null || true)"
  printf 'print_state=%s\n' "$STATE"
  case "$STATE" in
    printing|paused) printf 'blocked_printing=yes\n'; exit 23 ;;
  esac
else
  printf 'print_state=unknown\n'
fi

printf '\nSECTION backup\n'
mkdir -p "$BACKUP_DIR"
if [ -e "$SERVICE_PATH" ]; then
  sudo cp "$SERVICE_PATH" "$BACKUP_DIR/${IFACE}.service.before"
  printf 'backup=%s\n' "$BACKUP_DIR/${IFACE}.service.before"
else
  printf 'backup=none_existing_service\n'
fi

printf '\nSECTION write_service\n'
TMP_FILE="$(mktemp)"
cat > "$TMP_FILE" <<SERVICE
[Unit]
Description=Bring up ${IFACE} CAN interface for Klipper
After=network.target

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/sbin/ip link set ${IFACE} up type can bitrate ${BITRATE}
ExecStop=/sbin/ip link set ${IFACE} down

[Install]
WantedBy=multi-user.target
SERVICE
sudo install -m 0644 "$TMP_FILE" "$SERVICE_PATH"
rm -f "$TMP_FILE"
printf 'service=%s\n' "$SERVICE_PATH"

printf '\nSECTION systemd\n'
sudo systemctl daemon-reload
sudo systemctl enable "${IFACE}.service"
sudo systemctl restart "${IFACE}.service"
systemctl is-active "${IFACE}.service" 2>&1 || true

printf '\nSECTION validation\n'
ip -details -statistics link show "$IFACE" 2>&1
"""


class SetupCanRequest(BaseModel):
    target: SetupSshTarget
    interface_name: str = Field(default="can0", min_length=3, max_length=24)
    bitrate: int = Field(default=1000000, ge=10000, le=5000000)

    @field_validator("interface_name")
    @classmethod
    def _validate_interface(cls, value: str) -> str:
        cleaned = value.strip()
        if not re.fullmatch(r"[a-zA-Z0-9_.:-]+", cleaned):
            raise ValueError("interface_name inválida")
        return cleaned


class SetupCanApplyRequest(SetupCanRequest):
    confirmation: str = Field(min_length=1, max_length=80)


class SetupCanFinding(BaseModel):
    key: str
    status: SetupCanStatus
    title: str
    detail: str
    action: str


class SetupCanPreflightResponse(BaseModel):
    safe_mode: str
    connected: bool
    status: SetupCanStatus
    target: str
    interface_name: str
    bitrate: int
    summary: str
    findings: list[SetupCanFinding]
    sections: dict[str, str]
    parsed: dict[str, object]
    history_id: int | None = None
    error: str | None = None


class SetupCanPlanStep(BaseModel):
    key: str
    title: str
    status: Literal["ready", "missing", "manual", "blocked"]
    detail: str
    commands: list[SetupCommandPlan] = Field(default_factory=list)
    rollback: str | None = None


class SetupCanPlanResponse(BaseModel):
    safe_mode: str
    status: SetupCanStatus
    target: str
    interface_name: str
    bitrate: int
    summary: str
    preflight: SetupCanPreflightResponse
    steps: list[SetupCanPlanStep]
    blocked_reasons: list[str]
    history_id: int | None = None


class SetupCanApplyResponse(BaseModel):
    safe_mode: str
    status: SetupCanStatus
    target: str
    interface_name: str
    bitrate: int
    summary: str
    command_log: str
    validation: SetupCanPreflightResponse | None = None
    history_id: int | None = None
    blocked_reasons: list[str] = Field(default_factory=list)


class SetupCanRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_type: Literal["preflight", "plan", "apply"]
    status: SetupCanStatus
    safe_mode: str
    target_host: str
    target_port: int
    target_user: str
    interface_name: str
    bitrate: int
    summary: dict[str, object]
    plan: dict[str, object] | None
    command_log: str | None
    error_message: str | None
    created_at: str


@dataclass(frozen=True)
class SetupCanRunRepository:
    database_path: Path

    def create_preflight(self, request: SetupCanRequest, response: SetupCanPreflightResponse) -> int:
        return self._create_run(
            run_type="preflight",
            request=request,
            status=response.status,
            safe_mode=response.safe_mode,
            summary={"summary": response.summary, "findings": [finding.model_dump() for finding in response.findings]},
            plan=None,
            command_log=None,
            error=response.error,
        )

    def create_plan(self, request: SetupCanRequest, response: SetupCanPlanResponse) -> int:
        return self._create_run(
            run_type="plan",
            request=request,
            status=response.status,
            safe_mode=response.safe_mode,
            summary={"summary": response.summary, "blocked_reasons": response.blocked_reasons},
            plan={"steps": [step.model_dump() for step in response.steps]},
            command_log=None,
            error="; ".join(response.blocked_reasons) if response.blocked_reasons else None,
        )

    def create_apply(self, request: SetupCanRequest, response: SetupCanApplyResponse) -> int:
        return self._create_run(
            run_type="apply",
            request=request,
            status=response.status,
            safe_mode=response.safe_mode,
            summary={"summary": response.summary, "blocked_reasons": response.blocked_reasons},
            plan=None,
            command_log=response.command_log,
            error="; ".join(response.blocked_reasons) if response.blocked_reasons else None,
        )

    def list_runs(self, limit: int = 20) -> list[SetupCanRunRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, run_type, status, safe_mode, target_host, target_port, target_user,
                       interface_name, bitrate, summary_json, plan_json, command_log, error_message, created_at
                FROM setup_can_runs
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [_run_from_row(row) for row in rows]

    def _create_run(
        self,
        *,
        run_type: Literal["preflight", "plan", "apply"],
        request: SetupCanRequest,
        status: SetupCanStatus,
        safe_mode: str,
        summary: dict[str, object],
        plan: dict[str, object] | None,
        command_log: str | None,
        error: str | None,
    ) -> int:
        target = request.target
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO setup_can_runs (
                    run_type, status, safe_mode, target_host, target_port, target_user,
                    interface_name, bitrate, summary_json, plan_json, command_log, error_message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_type,
                    status,
                    safe_mode,
                    target.host,
                    target.port,
                    target.username,
                    request.interface_name,
                    request.bitrate,
                    json.dumps(summary, ensure_ascii=False),
                    json.dumps(plan, ensure_ascii=False) if plan is not None else None,
                    command_log,
                    error,
                ),
            )
            return int(cursor.lastrowid)


async def run_setup_can_preflight(request: SetupCanRequest) -> SetupCanPreflightResponse:
    result = await _run_remote_script(request, READ_ONLY_CAN_SCRIPT)
    if result["error"]:
        return SetupCanPreflightResponse(
            safe_mode="can_read_only_preflight",
            connected=False,
            status="error",
            target=_target_label(request.target),
            interface_name=request.interface_name,
            bitrate=request.bitrate,
            summary="Preflight CAN falhou antes da coleta read-only.",
            findings=[
                SetupCanFinding(
                    key="ssh",
                    status="error",
                    title="SSH indisponível",
                    detail=str(result["error"]),
                    action="Corrigir acesso SSH antes de preparar CAN.",
                )
            ],
            sections={},
            parsed={},
            error=str(result["error"]),
        )

    stdout = str(result["stdout"])
    stderr = str(result["stderr"])
    exit_code = int(result["exit_code"] or 0)
    sections = split_sections(stdout)
    parsed = parse_can_preflight_sections(sections)
    findings = build_can_findings(exit_code, sections, stderr, request.interface_name, request.bitrate)
    status = _overall_status(findings)
    connected = exit_code == 0
    return SetupCanPreflightResponse(
        safe_mode="can_read_only_preflight",
        connected=connected,
        status="error" if not connected else status,
        target=_target_label(request.target),
        interface_name=request.interface_name,
        bitrate=request.bitrate,
        summary=_summary(findings, connected),
        findings=findings,
        sections={name: _trim(value) for name, value in sections.items()},
        parsed=parsed,
        error=stderr.strip()[:500] if not connected and stderr.strip() else None,
    )


def build_setup_can_plan(preflight: SetupCanPreflightResponse) -> SetupCanPlanResponse:
    parsed = preflight.parsed
    blocked_reasons: list[str] = []
    if not preflight.connected:
        blocked_reasons.append("SSH indisponível para diagnóstico CAN.")
    if parsed.get("printing"):
        blocked_reasons.append("Impressão em andamento detectada; não preparar CAN durante impressão.")
    if parsed.get("systemd_available") is False:
        blocked_reasons.append("systemd não detectado; apply automático do serviço can0 não é suportado neste host.")

    iface = preflight.interface_name
    bitrate = preflight.bitrate
    steps = [
        SetupCanPlanStep(
            key="detect_u2c",
            title="Detectar U2C/USB-CAN",
            status="ready" if parsed.get("u2c_detected") else "missing",
            detail="U2C/USB-CAN detectado via USB." if parsed.get("u2c_detected") else "U2C/USB-CAN não apareceu no lsusb filtrado.",
            commands=[
                SetupCommandPlan(command="PLAN lsusb | egrep -i 'can|u2c|stm|bigtreetech'", risk="read_only", reason="Confirmar se o adaptador USB-CAN foi enumerado.")
            ],
        ),
        SetupCanPlanStep(
            key="load_can_modules",
            title="Validar módulos CAN",
            status="ready" if parsed.get("can_modules_loaded") else "missing",
            detail="Módulos CAN/gs_usb detectados." if parsed.get("can_modules_loaded") else "Módulos CAN/gs_usb não apareceram carregados.",
            commands=[
                SetupCommandPlan(command="PLAN sudo modprobe can", risk="mutable", reason="Carrega suporte CAN do kernel."),
                SetupCommandPlan(command="PLAN sudo modprobe can_raw", risk="mutable", reason="Carrega socket CAN raw usado pelo Klipper."),
                SetupCommandPlan(command="PLAN sudo modprobe gs_usb", risk="mutable", reason="Carrega driver comum de adaptadores USB-CAN como U2C."),
            ],
            rollback="Reiniciar host ou descarregar módulos manualmente se necessário.",
        ),
        SetupCanPlanStep(
            key="configure_can_service",
            title=f"Configurar {iface}.service",
            status="ready" if parsed.get("can_state") == "ERROR-ACTIVE" and parsed.get("bitrate") == bitrate else "missing",
            detail=(
                f"{iface} já está ERROR-ACTIVE com bitrate {bitrate}."
                if parsed.get("can_state") == "ERROR-ACTIVE" and parsed.get("bitrate") == bitrate
                else f"Preparar serviço systemd para subir {iface} com bitrate {bitrate}."
            ),
            commands=[
                SetupCommandPlan(command=f"PLAN backup /etc/systemd/system/{iface}.service", risk="mutable", reason="Preserva configuração anterior antes de alterar boot CAN."),
                SetupCommandPlan(command=f"PLAN escrever /etc/systemd/system/{iface}.service com ip link set {iface} up type can bitrate {bitrate}", risk="mutable", reason="Garante que a interface CAN suba no boot."),
                SetupCommandPlan(command=f"PLAN sudo systemctl enable --now {iface}.service", risk="mutable", reason="Ativa e valida a interface CAN."),
            ],
            rollback=f"Restaurar backup de /etc/systemd/system/{iface}.service e rodar sudo systemctl daemon-reload.",
        ),
        SetupCanPlanStep(
            key="validate_uuid",
            title="Validar UUIDs CAN",
            status="ready" if parsed.get("uuid_count", 0) > 0 else "manual",
            detail=(
                f"{parsed.get('uuid_count')} UUID(s) CAN encontrados."
                if parsed.get("uuid_count", 0) > 0
                else "UUIDs CAN ainda não foram encontrados ou Klipper tooling não está disponível."
            ),
            commands=[
                SetupCommandPlan(command=f"PLAN ~/klippy-env/bin/python ~/klipper/scripts/canbus_query.py {iface}", risk="read_only", reason="Consulta UUIDs CAN depois que can0 estiver online.")
            ],
        ),
    ]
    status: SetupCanStatus = "blocked" if blocked_reasons else "warning" if any(step.status in {"missing", "manual"} for step in steps) else "ok"
    return SetupCanPlanResponse(
        safe_mode="can_dry_run_plan",
        status=status,
        target=preflight.target,
        interface_name=iface,
        bitrate=bitrate,
        summary="Plano CAN bloqueado." if blocked_reasons else "Plano CAN dry-run pronto.",
        preflight=preflight,
        steps=steps,
        blocked_reasons=blocked_reasons,
    )


async def apply_setup_can(request: SetupCanApplyRequest) -> SetupCanApplyResponse:
    if request.confirmation != CAN_SETUP_CONFIRMATION:
        return _blocked_apply(request, ["Confirmação textual inválida."], "")
    if os.getenv(CAN_SETUP_MODE_ENV) != "remote":
        return _blocked_apply(
            request,
            [f"{CAN_SETUP_MODE_ENV}=remote não está habilitado."],
            "",
        )
    preflight = await run_setup_can_preflight(request)
    plan = build_setup_can_plan(preflight)
    if plan.blocked_reasons:
        return _blocked_apply(request, plan.blocked_reasons, "")

    result = await _run_remote_script(request, APPLY_CAN_SCRIPT, timeout_seconds=max(request.target.timeout_seconds, 20.0))
    command_log = _trim(f"{result['stdout']}\n{result['stderr']}", limit=6000)
    if result["error"]:
        return SetupCanApplyResponse(
            safe_mode="can_remote_apply",
            status="error",
            target=_target_label(request.target),
            interface_name=request.interface_name,
            bitrate=request.bitrate,
            summary="Apply CAN falhou antes da execução remota.",
            command_log=str(result["error"]),
            blocked_reasons=[str(result["error"])],
        )
    if int(result["exit_code"] or 0) != 0:
        return SetupCanApplyResponse(
            safe_mode="can_remote_apply",
            status="error",
            target=_target_label(request.target),
            interface_name=request.interface_name,
            bitrate=request.bitrate,
            summary=f"Apply CAN retornou erro exit_code={result['exit_code']}.",
            command_log=command_log,
            blocked_reasons=[f"exit_code={result['exit_code']}"],
        )
    validation = await run_setup_can_preflight(request)
    return SetupCanApplyResponse(
        safe_mode="can_remote_apply",
        status="ok" if validation.status == "ok" else "warning",
        target=_target_label(request.target),
        interface_name=request.interface_name,
        bitrate=request.bitrate,
        summary="Configuração CAN aplicada e validada." if validation.status == "ok" else "Configuração CAN aplicada com pendências de validação.",
        command_log=command_log,
        validation=validation,
    )


def parse_can_preflight_sections(sections: dict[str, str]) -> dict[str, object]:
    tools = _parse_tool_status(sections.get("tools", ""))
    can = sections.get("can", "")
    usb = sections.get("usb", "")
    modules = sections.get("modules", "")
    print_state = sections.get("print_state", "")
    uuid_query = sections.get("uuid_query", "")
    return {
        "tools": tools,
        "sudo_nopasswd": "sudo_nopasswd=yes" in sections.get("sudo", ""),
        "systemd_available": tools.get("systemctl") == "present" and "systemctl_unavailable" not in sections.get("services", ""),
        "u2c_detected": bool(re.search(r"u2c|bigtreetech|can", usb, re.IGNORECASE)),
        "can_modules_loaded": bool(re.search(r"(^|\s)(can|can_raw|can_dev|gs_usb)\b", modules, re.IGNORECASE | re.MULTILINE)),
        "can_state": _match_text(can, r"can state ([A-Z-]+)"),
        "bitrate": _match_int(can, r"bitrate\s+(\d+)"),
        "rx_errors": _match_int(can, r"RX:.*?\n\s*\d+\s+\d+\s+(\d+)", flags=re.DOTALL),
        "tx_errors": _match_int(can, r"TX:.*?\n\s*\d+\s+\d+\s+(\d+)", flags=re.DOTALL),
        "printing": bool(re.search(r'"state"\s*:\s*"(printing|paused)"', print_state)),
        "uuid_count": len(re.findall(r"canbus_uuid=([0-9a-fA-F]+)", uuid_query)),
        "config_service_present": f"present /etc/systemd/system/" in sections.get("config_files", ""),
    }


def build_can_findings(
    exit_code: int,
    sections: dict[str, str],
    stderr: str,
    interface_name: str,
    expected_bitrate: int,
) -> list[SetupCanFinding]:
    if exit_code != 0:
        return [
            SetupCanFinding(
                key="ssh",
                status="error",
                title="Coleta CAN falhou",
                detail=stderr.strip()[:300] or f"exit_code={exit_code}",
                action="Corrigir SSH antes de repetir.",
            )
        ]
    parsed = parse_can_preflight_sections(sections)
    tools = parsed["tools"] if isinstance(parsed["tools"], dict) else {}
    findings = [
        SetupCanFinding(
            key="ip_tool",
            status="ok" if tools.get("ip") == "present" else "error",
            title="Ferramenta ip",
            detail="iproute2 encontrado." if tools.get("ip") == "present" else "Comando ip não encontrado.",
            action="Instalar iproute2 antes de configurar CAN.",
        ),
        SetupCanFinding(
            key="u2c_usb",
            status="ok" if parsed.get("u2c_detected") else "warning",
            title="U2C/USB-CAN",
            detail="Adaptador compatível apareceu no USB filtrado." if parsed.get("u2c_detected") else "Nenhum U2C/USB-CAN apareceu no lsusb filtrado.",
            action="Validar cabo USB, alimentação e modo da placa.",
        ),
        SetupCanFinding(
            key="can_modules",
            status="ok" if parsed.get("can_modules_loaded") else "warning",
            title="Módulos CAN",
            detail="Módulos CAN ou gs_usb carregados." if parsed.get("can_modules_loaded") else "Módulos CAN/gs_usb não apareceram em lsmod.",
            action="Carregar can, can_raw e gs_usb antes do apply.",
        ),
        SetupCanFinding(
            key="can_interface",
            status="ok" if parsed.get("can_state") else "warning",
            title=f"Interface {interface_name}",
            detail=f"Estado CAN: {parsed.get('can_state')}." if parsed.get("can_state") else f"{interface_name} não foi encontrado pelo ip link.",
            action="Criar serviço de boot ou revisar U2C se a interface não existir.",
        ),
        SetupCanFinding(
            key="bitrate",
            status="ok" if parsed.get("bitrate") == expected_bitrate else "warning",
            title="Bitrate CAN",
            detail=f"Bitrate atual: {parsed.get('bitrate') or 'indisponível'}; esperado: {expected_bitrate}.",
            action="Ajustar bitrate para manter mainboard e toolhead na mesma velocidade.",
        ),
        SetupCanFinding(
            key="print_state",
            status="blocked" if parsed.get("printing") else "ok",
            title="Estado de impressão",
            detail="Impressão em andamento/pausada detectada." if parsed.get("printing") else "Nenhuma impressão em andamento detectada ou Moonraker indisponível.",
            action="Não alterar CAN durante impressão.",
        ),
        SetupCanFinding(
            key="uuid_query",
            status="ok" if parsed.get("uuid_count", 0) > 0 else "warning",
            title="UUIDs CAN",
            detail=f"{parsed.get('uuid_count')} UUID(s) encontrado(s)." if parsed.get("uuid_count", 0) > 0 else "Nenhum UUID CAN detectado nesta coleta.",
            action="Depois de can0 online, repetir query e validar placas.",
        ),
    ]
    return findings


async def _run_remote_script(
    request: SetupCanRequest,
    script: str,
    timeout_seconds: float | None = None,
) -> dict[str, object]:
    command = _ssh_command(request.target, request.interface_name, request.bitrate)
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
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(script.encode()),
            timeout=timeout_seconds or request.target.timeout_seconds,
        )
    except TimeoutError:
        process.kill()
        await process.wait()
        return {"stdout": "", "stderr": "", "exit_code": None, "error": f"Timeout de SSH após {(timeout_seconds or request.target.timeout_seconds):.0f}s."}
    return {
        "stdout": stdout_bytes.decode(errors="replace"),
        "stderr": stderr_bytes.decode(errors="replace"),
        "exit_code": process.returncode,
        "error": None,
    }


def _ssh_command(target: SetupSshTarget, interface_name: str, bitrate: int) -> list[str]:
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
    command.extend([
        f"{target.username}@{target.host}",
        f"PRINTORA_CAN_INTERFACE={interface_name} PRINTORA_CAN_BITRATE={bitrate} bash -s",
    ])
    return command


def _blocked_apply(request: SetupCanApplyRequest, reasons: list[str], command_log: str) -> SetupCanApplyResponse:
    return SetupCanApplyResponse(
        safe_mode="can_remote_apply_blocked",
        status="blocked",
        target=_target_label(request.target),
        interface_name=request.interface_name,
        bitrate=request.bitrate,
        summary="Apply CAN bloqueado.",
        command_log=command_log,
        blocked_reasons=reasons,
    )


def _run_from_row(row) -> SetupCanRunRecord:
    return SetupCanRunRecord(
        id=int(row["id"]),
        run_type=row["run_type"],
        status=row["status"],
        safe_mode=row["safe_mode"],
        target_host=row["target_host"],
        target_port=int(row["target_port"]),
        target_user=row["target_user"],
        interface_name=row["interface_name"],
        bitrate=int(row["bitrate"]),
        summary=json.loads(row["summary_json"]),
        plan=json.loads(row["plan_json"]) if row["plan_json"] else None,
        command_log=row["command_log"],
        error_message=row["error_message"],
        created_at=row["created_at"],
    )


def _parse_tool_status(section: str) -> dict[str, str]:
    tools: dict[str, str] = {}
    for line in section.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        tools[key.strip()] = "present" if value.startswith("present:") else "missing"
    return tools


def _overall_status(findings: list[SetupCanFinding]) -> SetupCanStatus:
    if any(finding.status == "error" for finding in findings):
        return "error"
    if any(finding.status == "blocked" for finding in findings):
        return "blocked"
    if any(finding.status == "warning" for finding in findings):
        return "warning"
    return "ok"


def _summary(findings: list[SetupCanFinding], connected: bool) -> str:
    if not connected:
        return "SSH indisponível para diagnóstico CAN."
    status = _overall_status(findings)
    if status == "ok":
        return "CAN/U2C validado sem pendências principais."
    return f"Diagnóstico CAN com {sum(1 for finding in findings if finding.status != 'ok')} pendência(s)."


def _trim(value: str, limit: int = 1800) -> str:
    cleaned = value.strip()
    return cleaned if len(cleaned) <= limit else f"{cleaned[:limit]}\n... truncado ..."


def _match_text(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text)
    return match.group(1) if match else None


def _match_int(text: str, pattern: str, flags: int = 0) -> int | None:
    match = re.search(pattern, text, flags=flags)
    if not match:
        return None
    try:
        return int(match.group(1))
    except ValueError:
        return None
