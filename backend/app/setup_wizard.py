from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.auth import scoped_where_clause
from app.database import connect_database


SetupAuthMethod = Literal["agent", "key_path"]
SetupRunStatus = Literal["ok", "warning", "error"]


READ_ONLY_SETUP_SCRIPT = r"""
set +e
printf 'SECTION host\n'
printf 'user='; id -un 2>&1
printf 'uid='; id -u 2>&1
printf 'groups='; id -Gn 2>&1
printf 'kernel='; uname -a 2>&1
printf 'arch='; uname -m 2>&1
printf 'pwd='; pwd 2>&1
printf 'home='; printf '%s\n' "$HOME"
printf '\nSECTION os\n'
cat /etc/os-release 2>&1
printf '\nSECTION tools\n'
for tool in bash git python3 python make gcc df curl systemctl ss ip lsusb; do
  if command -v "$tool" >/dev/null 2>&1; then
    printf '%s=present:%s\n' "$tool" "$(command -v "$tool")"
  else
    printf '%s=missing\n' "$tool"
  fi
done
printf '\nSECTION versions\n'
python3 --version 2>&1 || true
git --version 2>&1 || true
make --version 2>&1 | head -n 1 || true
gcc --version 2>&1 | head -n 1 || true
printf '\nSECTION disk\n'
df -h "$HOME" /tmp 2>&1
printf '\nSECTION ports\n'
if command -v ss >/dev/null 2>&1; then ss -ltnp 2>/dev/null | sed -n '1,80p'; else printf 'ss_unavailable\n'; fi
printf '\nSECTION services\n'
if command -v systemctl >/dev/null 2>&1; then
  systemctl list-units --type=service --all --no-pager 2>&1 | egrep -i 'klipper|moonraker|mainsail|nginx|crowsnest|printora' || true
else
  printf 'systemctl_unavailable\n'
fi
printf '\nSECTION paths\n'
for d in "$HOME/klipper" "$HOME/moonraker" "$HOME/mainsail" "$HOME/fluidd" "$HOME/printer_data" "$HOME/printer_data/config" "$HOME/Printora"; do
  if [ -e "$d" ]; then printf 'present %s\n' "$d"; else printf 'missing %s\n' "$d"; fi
done
printf '\nSECTION can\n'
if command -v ip >/dev/null 2>&1; then ip -details -statistics link show can0 2>&1; else printf 'ip_unavailable\n'; fi
printf '\nSECTION usb\n'
if command -v lsusb >/dev/null 2>&1; then lsusb 2>&1 | egrep -i 'can|u2c|stm|dfu|bigtreetech|katapult|klipper' || true; else printf 'lsusb_unavailable\n'; fi
"""


class SetupSshTarget(BaseModel):
    host: str = Field(min_length=1, max_length=160)
    port: int = Field(default=22, ge=1, le=65535)
    username: str = Field(min_length=1, max_length=80)
    auth_method: SetupAuthMethod = "agent"
    key_path: str | None = Field(default=None, max_length=260)
    timeout_seconds: float = Field(default=12.0, ge=2.0, le=60.0)

    @field_validator("host", "username")
    @classmethod
    def _validate_ssh_part(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned or re.search(r"\s", cleaned):
            raise ValueError("valor SSH não pode conter espaços")
        if any(char in cleaned for char in [";", "&", "|", "$", "`", "<", ">"]):
            raise ValueError("valor SSH contém caractere não permitido")
        return cleaned

    @field_validator("key_path")
    @classmethod
    def _validate_key_path(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            return None
        if "\n" in cleaned or "\r" in cleaned:
            raise ValueError("key_path inválido")
        return cleaned


class SetupCheckItem(BaseModel):
    key: str
    label: str
    status: SetupRunStatus
    detail: str


class SetupCommandPlan(BaseModel):
    command: str
    risk: Literal["read_only", "mutable", "manual"]
    reason: str


class SetupPlanStep(BaseModel):
    key: str
    title: str
    status: Literal["ready", "missing", "manual", "blocked"]
    detail: str
    commands: list[SetupCommandPlan] = Field(default_factory=list)
    rollback: str | None = None


class SetupSshPreflightResponse(BaseModel):
    safe_mode: str
    connected: bool
    status: SetupRunStatus
    target: str
    summary: str
    checks: list[SetupCheckItem]
    sections: dict[str, str]
    redacted_target: dict[str, object]
    history_id: int | None = None
    error: str | None = None


class SetupSshPlanResponse(BaseModel):
    safe_mode: str
    status: SetupRunStatus
    target: str
    summary: str
    preflight: SetupSshPreflightResponse
    steps: list[SetupPlanStep]
    blocked_reasons: list[str]
    history_id: int | None = None


class SetupSshRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_type: Literal["preflight", "plan"]
    status: SetupRunStatus
    safe_mode: str
    target_host: str
    target_port: int
    target_user: str
    auth_method: SetupAuthMethod
    summary: dict[str, object]
    plan: dict[str, object] | None
    error_message: str | None
    created_at: str


@dataclass(frozen=True)
class SetupSshRunRepository:
    database_path: Path
    user_id: int | None = None
    organization_ids: tuple[int, ...] = ()

    def create_preflight(self, target: SetupSshTarget, response: SetupSshPreflightResponse) -> int:
        return self._create_run(
            run_type="preflight",
            target=target,
            status=response.status,
            safe_mode=response.safe_mode,
            summary={
                "connected": response.connected,
                "summary": response.summary,
                "checks": [check.model_dump() for check in response.checks],
            },
            plan=None,
            error=response.error,
        )

    def create_plan(self, target: SetupSshTarget, response: SetupSshPlanResponse) -> int:
        return self._create_run(
            run_type="plan",
            target=target,
            status=response.status,
            safe_mode=response.safe_mode,
            summary={
                "summary": response.summary,
                "blocked_reasons": response.blocked_reasons,
                "preflight_history_id": response.preflight.history_id,
            },
            plan={"steps": [step.model_dump() for step in response.steps]},
            error="; ".join(response.blocked_reasons) if response.blocked_reasons else None,
        )

    def list_runs(self, limit: int = 20) -> list[SetupSshRunRecord]:
        with connect_database(self.database_path) as connection:
            where_clause, params = _scope_sql("setup_ssh_runs", self.user_id, self.organization_ids)
            rows = connection.execute(
                f"""
                SELECT id, run_type, status, safe_mode, target_host, target_port, target_user,
                       auth_method, summary_json, plan_json, error_message, created_at
                FROM setup_ssh_runs
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
        run_type: Literal["preflight", "plan"],
        target: SetupSshTarget,
        status: SetupRunStatus,
        safe_mode: str,
        summary: dict[str, object],
        plan: dict[str, object] | None,
        error: str | None,
    ) -> int:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO setup_ssh_runs (
                    run_type, status, safe_mode, target_host, target_port, target_user,
                    auth_method, summary_json, plan_json, error_message, owner_user_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_type,
                    status,
                    safe_mode,
                    target.host,
                    target.port,
                    target.username,
                    target.auth_method,
                    json.dumps(summary, ensure_ascii=False),
                    json.dumps(plan, ensure_ascii=False) if plan is not None else None,
                    error,
                    self.user_id,
                ),
            )
            return int(cursor.lastrowid)


async def run_setup_ssh_preflight(target: SetupSshTarget) -> SetupSshPreflightResponse:
    if target.auth_method == "agent":
        from app.agent_host import run_host_script_via_agent

        result = await run_host_script_via_agent(
            target,
            READ_ONLY_SETUP_SCRIPT,
            timeout_seconds=target.timeout_seconds,
            kind="setup_ssh_preflight",
        )
        stdout = str(result.get("stdout") or "")
        stderr = str(result.get("stderr") or "")
        exit_code = result.get("exit_code")
        error = str(result.get("error") or "")
        sections = split_sections(stdout)
        checks = build_setup_checks(int(exit_code or 1), sections, stderr or error)
        status = _overall_status(checks)
        connected = exit_code == 0 and not error
        return SetupSshPreflightResponse(
            safe_mode="agent_read_only_preflight",
            connected=connected,
            status="error" if not connected else status,
            target=_target_label(target),
            summary=_preflight_summary(connected, status, checks),
            checks=checks,
            sections={name: _trim_section(value) for name, value in sections.items()},
            redacted_target=_redacted_target(target),
            error=(error or stderr.strip())[:500] if not connected and (error or stderr.strip()) else None,
        )

    return _connection_error(target, "Acesso SSH direto pela API foi desativado para cloud. Use auth_method=agent com agente pareado.")


def build_setup_plan(preflight: SetupSshPreflightResponse) -> SetupSshPlanResponse:
    checks_by_key = {check.key: check for check in preflight.checks}
    blocked_reasons: list[str] = []
    steps: list[SetupPlanStep] = [
        SetupPlanStep(
            key="prepare_os_media",
            title="Preparar boot inicial",
            status="manual",
            detail="Placa virgem não aceita SSH. Grave uma imagem Linux compatível, configure rede e habilite SSH antes deste wizard.",
            commands=[],
            rollback="Regravar o SD/eMMC com a imagem anterior ou restaurar backup da mídia.",
        )
    ]

    if not preflight.connected:
        blocked_reasons.append("SSH não conectado. Corrija rede, usuário, porta ou chave antes do provisionamento.")
        steps.append(
            SetupPlanStep(
                key="fix_ssh_access",
                title="Corrigir acesso SSH",
                status="blocked",
                detail=preflight.error or "Preflight SSH falhou.",
                commands=[
                    SetupCommandPlan(
                        command="PLAN validar IP/hostname, usuário, porta 22 e chave SSH pelo computador do operador",
                        risk="manual",
                        reason="Sem SSH ativo não há canal seguro para provisionamento remoto.",
                    )
                ],
            )
        )
        return _plan_response(preflight, steps, blocked_reasons)

    tools = _parse_tool_status(preflight.sections.get("tools", ""))
    paths = preflight.sections.get("paths", "")
    services = preflight.sections.get("services", "")
    has_systemd = tools.get("systemctl") == "present" and "systemctl_unavailable" not in services
    missing_base_tools = [tool for tool in ["git", "python3", "make", "gcc", "curl"] if tools.get(tool) != "present"]

    steps.append(
        SetupPlanStep(
            key="install_base_dependencies",
            title="Dependências base do host",
            status="missing" if missing_base_tools else "ready",
            detail=(
                f"Faltando: {', '.join(missing_base_tools)}."
                if missing_base_tools
                else "Ferramentas base encontradas para preparar Klipper/Moonraker."
            ),
            commands=[
                SetupCommandPlan(
                    command="PLAN sudo apt update",
                    risk="mutable",
                    reason="Atualiza índice de pacotes antes de instalar dependências.",
                ),
                SetupCommandPlan(
                    command="PLAN sudo apt install -y git python3 python3-venv python3-dev make gcc curl",
                    risk="mutable",
                    reason="Instala dependências comuns de Klipper/Moonraker.",
                ),
            ] if missing_base_tools else [],
            rollback="Remover pacotes instalados manualmente se a etapa for revertida.",
        )
    )
    steps.append(
        SetupPlanStep(
            key="install_klipper",
            title="Instalar Klipper",
            status="ready" if "present" in _path_line(paths, "klipper") else "missing",
            detail="Klipper já existe no host." if "present" in _path_line(paths, "klipper") else "Klipper não foi encontrado em ~/klipper.",
            commands=[
                SetupCommandPlan(
                    command="PLAN git clone https://github.com/Klipper3d/klipper ~/klipper",
                    risk="mutable",
                    reason="Baixa Klipper no path padrão do usuário SSH.",
                ),
                SetupCommandPlan(
                    command="PLAN ~/klipper/scripts/install-octopi.sh",
                    risk="mutable",
                    reason="Prepara serviço e ambiente Python do Klipper.",
                ),
            ],
            rollback="Parar serviço klipper e remover diretórios criados somente após backup dos configs.",
        )
    )
    steps.append(
        SetupPlanStep(
            key="install_moonraker",
            title="Instalar Moonraker",
            status="ready" if "moonraker" in services.lower() or "present" in _path_line(paths, "moonraker") else "missing",
            detail="Moonraker detectado." if "moonraker" in services.lower() or "present" in _path_line(paths, "moonraker") else "Moonraker não foi encontrado.",
            commands=[
                SetupCommandPlan(
                    command="PLAN git clone https://github.com/Arksine/moonraker ~/moonraker",
                    risk="mutable",
                    reason="Baixa Moonraker no path padrão.",
                ),
                SetupCommandPlan(
                    command="PLAN ~/moonraker/scripts/install-moonraker.sh",
                    risk="mutable",
                    reason="Prepara serviço Moonraker.",
                ),
            ],
            rollback="Parar serviço moonraker e restaurar configuração anterior.",
        )
    )
    steps.append(
        SetupPlanStep(
            key="install_web_ui",
            title="Instalar Mainsail/Fluidd",
            status="ready" if re.search(r"mainsail|fluidd", services, re.IGNORECASE) or re.search(r"present .*/(mainsail|fluidd)", paths) else "missing",
            detail="Interface web detectada." if re.search(r"mainsail|fluidd", services, re.IGNORECASE) else "Mainsail/Fluidd não detectado.",
            commands=[
                SetupCommandPlan(
                    command="PLAN instalar Mainsail via pacote/release compatível com a distribuição",
                    risk="mutable",
                    reason="Adiciona UI web para operação Klipper.",
                )
            ],
            rollback="Restaurar configuração do servidor web e remover arquivos da UI instalada.",
        )
    )
    steps.append(
        SetupPlanStep(
            key="install_printora",
            title="Instalar Printora",
            status="ready" if "present" in _path_line(paths, "Printora") else "missing",
            detail="Printora já existe no host." if "present" in _path_line(paths, "Printora") else "Printora não foi encontrado no host.",
            commands=[
                SetupCommandPlan(
                    command="PLAN git clone https://github.com/mayder/printora.git ~/Printora",
                    risk="mutable",
                    reason="Baixa Printora para instalação local.",
                ),
                SetupCommandPlan(
                    command="PLAN cd ~/Printora && ./scripts/install-linux.sh",
                    risk="mutable",
                    reason="Instala Printora com serviço local.",
                ),
            ],
            rollback="Usar scripts oficiais de rollback/update ou remover serviço Printora após backup do banco.",
        )
    )
    steps.append(
        SetupPlanStep(
            key="prepare_can",
            title="Preparar CAN/U2C",
            status="ready" if _can0_online(preflight.sections.get("can", "")) else "missing",
            detail="can0 detectado no host." if _can0_online(preflight.sections.get("can", "")) else "can0 ainda não está online ou não existe.",
            commands=[
                SetupCommandPlan(
                    command="PLAN diagnosticar U2C, configurar can0 e validar bitrate",
                    risk="manual",
                    reason="Setup CAN exige backup/rollback específico antes de aplicar mudanças.",
                )
            ],
            rollback="Restaurar arquivos de rede/systemd alterados pelo pacote CAN.",
        )
    )
    steps.append(
        SetupPlanStep(
            key="firmware_next",
            title="Firmware e flash",
            status="manual",
            detail="Build, UUID e flash ficam nas etapas supervisionadas depois do host provisionado.",
            commands=[
                SetupCommandPlan(
                    command="PLAN seguir wizard de firmware com Octopus/EBB/U2C ou outro hardware confirmado",
                    risk="manual",
                    reason="Firmware depende da placa física escolhida e de confirmação do operador.",
                )
            ],
            rollback="Usar rollback manual de firmware por placa.",
        )
    )

    if not has_systemd:
        blocked_reasons.append("systemd não detectado. Instalação automática de serviços precisa de estratégia específica para este SO.")
    return _plan_response(preflight, steps, blocked_reasons)


def split_sections(output: str) -> dict[str, str]:
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


def build_setup_checks(exit_code: int, sections: dict[str, str], stderr: str = "") -> list[SetupCheckItem]:
    if exit_code != 0:
        return [
            SetupCheckItem(
                key="ssh",
                label="Conexão SSH",
                status="error",
                detail=stderr.strip()[:300] or f"ssh exit_code={exit_code}",
            )
        ]
    tools = _parse_tool_status(sections.get("tools", ""))
    paths = sections.get("paths", "")
    services = sections.get("services", "")
    can = sections.get("can", "")
    return [
        SetupCheckItem(key="ssh", label="Conexão SSH", status="ok", detail="Comando read-only executado com sucesso."),
        SetupCheckItem(key="os", label="Sistema operacional", status="ok" if sections.get("os") else "warning", detail=_os_detail(sections.get("os", ""))),
        SetupCheckItem(key="systemd", label="systemd", status="ok" if tools.get("systemctl") == "present" else "warning", detail=_tool_detail(tools, "systemctl")),
        SetupCheckItem(key="base_tools", label="Ferramentas base", status="ok" if all(tools.get(tool) == "present" for tool in ["git", "python3", "curl"]) else "warning", detail=_missing_tools_detail(tools, ["git", "python3", "curl"])),
        SetupCheckItem(key="build_tools", label="Ferramentas de build", status="ok" if all(tools.get(tool) == "present" for tool in ["make", "gcc"]) else "warning", detail=_missing_tools_detail(tools, ["make", "gcc"])),
        SetupCheckItem(key="klipper", label="Klipper", status="ok" if "present" in _path_line(paths, "klipper") or "klipper" in services.lower() else "warning", detail=_component_detail(paths, services, "klipper")),
        SetupCheckItem(key="moonraker", label="Moonraker", status="ok" if "present" in _path_line(paths, "moonraker") or "moonraker" in services.lower() else "warning", detail=_component_detail(paths, services, "moonraker")),
        SetupCheckItem(key="printer_data", label="printer_data", status="ok" if "present" in _path_line(paths, "printer_data") else "warning", detail=_path_line(paths, "printer_data") or "Diretório printer_data não encontrado."),
        SetupCheckItem(key="can0", label="CAN can0", status="ok" if _can0_online(can) else "warning", detail=_trim_section(can) or "can0 não detectado."),
    ]


def _connection_error(target: SetupSshTarget, detail: str) -> SetupSshPreflightResponse:
    check = SetupCheckItem(key="ssh", label="Conexão SSH", status="error", detail=detail)
    return SetupSshPreflightResponse(
        safe_mode="ssh_read_only_preflight",
        connected=False,
        status="error",
        target=_target_label(target),
        summary="SSH indisponível. Nenhuma alteração foi aplicada.",
        checks=[check],
        sections={},
        redacted_target=_redacted_target(target),
        error=detail,
    )


def _plan_response(
    preflight: SetupSshPreflightResponse,
    steps: list[SetupPlanStep],
    blocked_reasons: list[str],
) -> SetupSshPlanResponse:
    missing_count = sum(1 for step in steps if step.status == "missing")
    status: SetupRunStatus = "error" if blocked_reasons and not preflight.connected else "warning" if blocked_reasons or missing_count else "ok"
    summary = (
        "Plano bloqueado até corrigir o acesso SSH."
        if not preflight.connected
        else f"Plano dry-run pronto com {missing_count} etapa(s) a instalar/configurar."
    )
    return SetupSshPlanResponse(
        safe_mode="ssh_dry_run_plan",
        status=status,
        target=preflight.target,
        summary=summary,
        preflight=preflight,
        steps=steps,
        blocked_reasons=blocked_reasons,
    )


def _run_from_row(row) -> SetupSshRunRecord:
    return SetupSshRunRecord(
        id=int(row["id"]),
        run_type=row["run_type"],
        status=row["status"],
        safe_mode=row["safe_mode"],
        target_host=row["target_host"],
        target_port=int(row["target_port"]),
        target_user=row["target_user"],
        auth_method=row["auth_method"],
        summary=json.loads(row["summary_json"]),
        plan=json.loads(row["plan_json"]) if row["plan_json"] else None,
        error_message=row["error_message"],
        created_at=row["created_at"],
    )


def _scope_sql(table_alias: str, user_id: int | None, organization_ids: tuple[int, ...]) -> tuple[str, tuple[object, ...]]:
    if user_id is None:
        return "", ()
    return scoped_where_clause(table_alias, user_id, organization_ids)


def _parse_tool_status(section: str) -> dict[str, str]:
    tools: dict[str, str] = {}
    for line in section.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        tools[key.strip()] = "present" if value.startswith("present:") else "missing"
    return tools


def _overall_status(checks: list[SetupCheckItem]) -> SetupRunStatus:
    if any(check.status == "error" for check in checks):
        return "error"
    if any(check.status == "warning" for check in checks):
        return "warning"
    return "ok"


def _preflight_summary(connected: bool, status: SetupRunStatus, checks: list[SetupCheckItem]) -> str:
    if not connected:
        return "SSH indisponível. Nenhuma alteração foi aplicada."
    warnings = sum(1 for check in checks if check.status == "warning")
    if status == "ok":
        return "Host acessível e pronto para plano de provisionamento."
    return f"Host acessível com {warnings} ponto(s) a preparar antes da instalação completa."


def _target_label(target: SetupSshTarget) -> str:
    return f"{target.username}@{target.host}:{target.port}"


def _redacted_target(target: SetupSshTarget) -> dict[str, object]:
    return {
        "host": target.host,
        "port": target.port,
        "username": target.username,
        "auth_method": target.auth_method,
        "key_path_configured": bool(target.key_path),
    }


def _trim_section(value: str, limit: int = 1800) -> str:
    cleaned = value.strip()
    return cleaned if len(cleaned) <= limit else f"{cleaned[:limit]}\n... truncado ..."


def _os_detail(section: str) -> str:
    pretty = re.search(r'^PRETTY_NAME="?([^"\n]+)"?', section, flags=re.MULTILINE)
    return pretty.group(1) if pretty else "Arquivo /etc/os-release não retornou nome do SO."


def _tool_detail(tools: dict[str, str], tool: str) -> str:
    return "Encontrado." if tools.get(tool) == "present" else "Não encontrado."


def _missing_tools_detail(tools: dict[str, str], expected: list[str]) -> str:
    missing = [tool for tool in expected if tools.get(tool) != "present"]
    return "Todas encontradas." if not missing else f"Faltando: {', '.join(missing)}."


def _component_detail(paths: str, services: str, name: str) -> str:
    path_line = _path_line(paths, name)
    service_hit = name in services.lower()
    if path_line and service_hit:
        return f"{path_line}; serviço detectado."
    if path_line:
        return path_line
    if service_hit:
        return "Serviço detectado."
    return f"{name} não detectado."


def _path_line(paths: str, needle: str) -> str:
    for line in paths.splitlines():
        if needle.lower() in line.lower():
            return line.strip()
    return ""


def _can0_online(section: str) -> bool:
    return "can state ERROR-ACTIVE" in section or "state UP" in section or "ERROR-ACTIVE" in section
