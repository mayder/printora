import asyncio
import re
from dataclasses import dataclass
from typing import Literal

from app.audit import AuditFinding


HostAuditMode = Literal["disabled", "local", "ssh"]


READ_ONLY_SCRIPT = r"""
set +e
printf 'SECTION host\n'
printf 'user='; id -un 2>&1
printf 'uid='; id -u 2>&1
printf 'kernel='; uname -a 2>&1
printf 'pwd='; pwd 2>&1
printf '\nSECTION runtime\n'
python --version 2>&1 || python3 --version 2>&1 || true
node --version 2>&1 || true
npm --version 2>&1 || true
printf '\nSECTION disk\n'
df -h . "$HOME" 2>&1
printf 'SECTION printer_info\n'
curl -fsS http://127.0.0.1:7125/printer/info 2>&1
printf '\nSECTION print_stats\n'
curl -fsS 'http://127.0.0.1:7125/printer/objects/query?print_stats' 2>&1
printf '\nSECTION systemctl_failed\n'
if command -v systemctl >/dev/null 2>&1; then systemctl --failed --no-pager 2>&1; else printf 'systemctl_unavailable\n'; fi
printf '\nSECTION relevant_services\n'
if command -v systemctl >/dev/null 2>&1; then systemctl list-units --type=service --all --no-pager 2>&1 | egrep -i 'klipper|moonraker|mainsail|crowsnest|sonar|spoolman|ustreamer|webcam|camera|mayder|nginx' || true; else printf 'systemctl_unavailable\n'; fi
printf '\nSECTION can0\n'
if command -v ip >/dev/null 2>&1; then ip -details -statistics link show can0 2>&1; else printf 'can0_unavailable\n'; fi
printf '\nSECTION active_includes\n'
if [ -d /home/pi/printer_data/config ]; then grep -RIn --include='*.cfg' '^\[include ' /home/pi/printer_data/config 2>&1 | grep -v '/backups/' | sed -n '1,220p'; else printf 'printer_config_unavailable\n'; fi
printf '\nSECTION active_legacy_refs\n'
if [ -d /home/pi/printer_data/config ]; then grep -RInE 'tapchanger|auto_speed|sonar|crowsnest|timelapse|tmc_autotune' /home/pi/printer_data/config --include='*.cfg' --exclude-dir=backups --exclude='printer-*.cfg' 2>&1 || true; fi
printf '\nSECTION active_broken_symlinks\n'
if [ -d /home/pi/printer_data/config ]; then find /home/pi/printer_data/config -path '*/backups/*' -prune -o -xtype l -print 2>&1; fi
printf '\nSECTION extras_symlinks\n'
if [ -d /home/pi/klipper/klippy/extras ]; then find /home/pi/klipper/klippy/extras -maxdepth 1 \( -type l -o -type f \) -printf '%M %p -> %l\n' 2>&1 | egrep -i 'ktc|tool|probe|tap|kamp|adaptive|led|auto|sonar|speed|timelapse|autotune' || true; fi
printf '\nSECTION config_git\n'
if [ -d /home/pi/printer_data/config/.git ]; then git -C /home/pi/printer_data/config status --short --branch 2>&1; fi
printf '\nSECTION repos\n'
for d in /home/pi/klipper /home/pi/moonraker /home/pi/mainsail-config /home/pi/klipper-led_effect /home/pi/klipper-toolchanger-easy /home/pi/adaptive_meshing_purging /home/pi/spoolman /home/pi/crowsnest /home/pi/sonar /home/pi/timelapse /home/pi/auto_speed /home/pi/tmc_autotune; do
  if [ -d "$d/.git" ]; then
    printf 'REPO %s\n' "$d"
    git -C "$d" status --short --branch 2>&1
    git -C "$d" describe --tags --always --dirty 2>&1
  elif [ -e "$d" ]; then
    printf 'LEGACY_PATH %s\n' "$d"
  fi
done
printf '\nSECTION recent_klippy_log\n'
tail -n 1600 /home/pi/printer_data/logs/klippy.log 2>/dev/null | grep -aEi 'error|traceback|exception|deprecated|warning|disconnect|timeout|shutdown|canstat|dirty|probe samples|bytes_invalid' | tail -n 80
printf '\nSECTION recent_moonraker_log\n'
tail -n 1200 /home/pi/printer_data/logs/moonraker.log 2>/dev/null | grep -aEi 'error|traceback|exception|warning|failed|dirty|crowsnest|sonar|timelapse|spoolman' | tail -n 80
"""


@dataclass(frozen=True)
class HostAuditResult:
    mode: HostAuditMode
    executed: bool
    exit_code: int | None
    stdout: str
    stderr: str
    sections: dict[str, str]
    findings: list[AuditFinding]


async def collect_host_audit(
    mode: HostAuditMode,
    ssh_target: str,
    timeout_seconds: float,
) -> HostAuditResult:
    if mode == "disabled":
        return HostAuditResult(
            mode=mode,
            executed=False,
            exit_code=None,
            stdout="",
            stderr="",
            sections={},
            findings=[
                AuditFinding(
                    id="host_audit_disabled",
                    title="Auditoria do host desabilitada",
                    category="host",
                    classification="precisa_confirmacao",
                    severity="info",
                    detail="Configure host_audit_mode=local ou host_audit_mode=ssh para coletar dados do host.",
                    safe_action="Em produção na Raspberry, preferir modo local. Em desenvolvimento, usar SSH com chave.",
                )
            ],
        )

    command = _build_command(mode, ssh_target)
    process = await asyncio.create_subprocess_exec(
        *command,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(READ_ONLY_SCRIPT.encode()),
            timeout=timeout_seconds,
        )
    except TimeoutError:
        process.kill()
        await process.wait()
        return HostAuditResult(
            mode=mode,
            executed=True,
            exit_code=None,
            stdout="",
            stderr="timeout",
            sections={},
            findings=[
                AuditFinding(
                    id="host_audit_timeout",
                    title="Auditoria do host excedeu o tempo limite",
                    category="host",
                    classification="precisa_confirmacao",
                    severity="warning",
                    detail=f"timeout_seconds={timeout_seconds}",
                    safe_action="Aumentar timeout ou validar conectividade SSH. Nenhuma alteração foi aplicada.",
                )
            ],
        )

    stdout = stdout_bytes.decode(errors="replace")
    stderr = stderr_bytes.decode(errors="replace")
    sections = split_sections(stdout)
    findings = build_host_findings(process.returncode or 0, sections, stderr)
    return HostAuditResult(
        mode=mode,
        executed=True,
        exit_code=process.returncode,
        stdout=stdout,
        stderr=stderr,
        sections=sections,
        findings=findings,
    )


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
    return {name: "\n".join(lines).strip() for name, lines in sections.items()}


def build_host_findings(exit_code: int, sections: dict[str, str], stderr: str = "") -> list[AuditFinding]:
    findings: list[AuditFinding] = []
    if exit_code != 0:
        findings.append(
            AuditFinding(
                id="host_audit_command_failed",
                title="Coleta read-only do host retornou erro",
                category="host",
                classification="precisa_confirmacao",
                severity="warning",
                detail=f"exit_code={exit_code} stderr={stderr[:300]}",
                safe_action="Validar conectividade e permissões. A coleta não executa comandos mutáveis.",
            )
        )

    _audit_systemctl(findings, sections.get("systemctl_failed", ""))
    _audit_can(findings, sections.get("can0", ""))
    _audit_legacy_refs(findings, sections.get("active_legacy_refs", ""))
    _audit_broken_symlinks(findings, sections.get("active_broken_symlinks", ""))
    _audit_git(findings, sections.get("config_git", ""), sections.get("repos", ""))
    _audit_logs(findings, sections.get("recent_klippy_log", ""), sections.get("recent_moonraker_log", ""))

    if not findings:
        findings.append(
            AuditFinding(
                id="host_audit_no_findings",
                title="Auditoria do host sem achados críticos",
                category="host",
                classification="ignorar",
                severity="info",
                detail="Systemd, CAN, refs antigas, symlinks e repos não indicaram bloqueios.",
                safe_action="Continuar usando como baseline antes/depois de updates.",
            )
        )
    return findings


def summarize_sections(sections: dict[str, str]) -> dict[str, object]:
    can = sections.get("can0", "")
    return {
        "systemctl_failed": _one_line(sections.get("systemctl_failed", "")),
        "can": parse_can_summary(can),
        "config_git": sections.get("config_git", "").splitlines()[:8],
        "legacy_refs_count": _non_empty_line_count(sections.get("active_legacy_refs", "")),
        "broken_symlink_count": _non_empty_line_count(sections.get("active_broken_symlinks", "")),
        "repo_count": len(re.findall(r"^REPO ", sections.get("repos", ""), flags=re.MULTILINE)),
        "legacy_path_count": len(re.findall(r"^LEGACY_PATH ", sections.get("repos", ""), flags=re.MULTILINE)),
    }


def parse_can_summary(can_output: str) -> dict[str, object]:
    return {
        "state": _match_text(can_output, r"can state ([A-Z-]+)"),
        "rx_errors": _match_int(can_output, r"RX:.*?\n\s*\d+\s+\d+\s+(\d+)", flags=re.DOTALL),
        "tx_errors": _match_int(can_output, r"TX:.*?\n\s*\d+\s+\d+\s+(\d+)", flags=re.DOTALL),
        "bus_errors": _match_int(can_output, r"bus-errors.*?\n\s*\d+\s+(\d+)", flags=re.DOTALL),
    }


def _build_command(mode: HostAuditMode, ssh_target: str) -> list[str]:
    if mode == "local":
        return ["bash", "-s"]
    return [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=5",
        ssh_target,
        "bash -s",
    ]


def _audit_systemctl(findings: list[AuditFinding], section: str) -> None:
    if "0 loaded units listed" in section:
        return
    failed_lines = [line for line in section.splitlines() if ".service" in line and "failed" in line.lower()]
    if failed_lines:
        findings.append(
            AuditFinding(
                id="systemd_failed_units",
                title="Há serviços systemd falhando",
                category="systemd",
                classification="corrigir_agora",
                severity="blocker",
                detail="; ".join(failed_lines[:5]),
                safe_action="Inspecionar logs dos serviços antes de imprimir ou atualizar.",
            )
        )


def _audit_can(findings: list[AuditFinding], section: str) -> None:
    if (
        not section
        or "can0_unavailable" in section
        or "Device \"can0\" does not exist" in section
        or "Cannot find device \"can0\"" in section
    ):
        return
    if "not found" in section.lower():
        findings.append(
            AuditFinding(
                id="can0_missing",
                title="Dados CAN não foram coletados",
                category="can",
                classification="precisa_confirmacao",
                severity="warning",
                detail="A seção can0 veio vazia.",
                safe_action="Validar se a interface CAN está disponível no host.",
            )
        )
        return
    summary = parse_can_summary(section)
    if summary["state"] is None:
        return
    if summary["state"] not in {"ERROR-ACTIVE", "ACTIVE"}:
        findings.append(
            AuditFinding(
                id="can0_state_not_active",
                title="CAN não está em estado ativo",
                category="can",
                classification="corrigir_agora",
                severity="blocker",
                detail=str(summary),
                safe_action="Verificar cabo CAN, terminação, alimentação, aterramento e bitrate.",
            )
        )
    if any((summary.get(key) or 0) > 0 for key in ["rx_errors", "tx_errors", "bus_errors"]):
        findings.append(
            AuditFinding(
                id="can0_errors_detected",
                title="CAN tem contadores de erro",
                category="can",
                classification="monitorar",
                severity="warning",
                detail=str(summary),
                safe_action="Monitorar se os contadores crescem entre impressões.",
            )
        )


def _audit_legacy_refs(findings: list[AuditFinding], section: str) -> None:
    if not section:
        return
    findings.append(
        AuditFinding(
            id="active_legacy_plugin_refs",
            title="Referências ativas a plugins legados",
            category="config",
            classification="precisa_confirmacao",
            severity="warning",
            detail="; ".join(section.splitlines()[:8]),
            safe_action="Confirmar se as referências são necessárias antes de remover.",
        )
    )


def _audit_broken_symlinks(findings: list[AuditFinding], section: str) -> None:
    if not section:
        return
    findings.append(
        AuditFinding(
            id="active_broken_symlinks",
            title="Symlinks quebrados em configs ativas",
            category="config",
            classification="corrigir_agora",
            severity="blocker",
            detail="; ".join(section.splitlines()[:8]),
            safe_action="Corrigir ou arquivar links quebrados antes de novos updates.",
        )
    )


def _audit_git(findings: list[AuditFinding], config_git: str, repos: str) -> None:
    dirty_config = [line for line in config_git.splitlines() if line and not line.startswith("## ")]
    if dirty_config:
        findings.append(
            AuditFinding(
                id="config_repo_dirty",
                title="Repo de configuração tem alterações não commitadas",
                category="git",
                classification="monitorar",
                severity="warning",
                detail="; ".join(dirty_config[:8]),
                safe_action="Versionar mudanças intencionais ou revisar antes de alterar configs.",
            )
        )
    legacy_paths = [line.removeprefix("LEGACY_PATH ").strip() for line in repos.splitlines() if line.startswith("LEGACY_PATH ")]
    if legacy_paths:
        findings.append(
            AuditFinding(
                id="legacy_paths_present",
                title="Há diretórios legados fora do uso ativo",
                category="git",
                classification="monitorar",
                severity="info",
                detail="; ".join(legacy_paths[:8]),
                safe_action="Remover somente depois de confirmação e backup.",
            )
        )


def _audit_logs(findings: list[AuditFinding], klippy_log: str, moonraker_log: str) -> None:
    severe = _filtered_log_lines(klippy_log, ["traceback", "shutdown", "exception"])
    if severe:
        findings.append(
            AuditFinding(
                id="recent_klippy_severe_log",
                title="Klippy tem erro severo recente nos logs filtrados",
                category="logs",
                classification="precisa_confirmacao",
                severity="warning",
                detail="; ".join(severe[:5]),
                safe_action="Abrir trecho completo do klippy.log antes de alterar configuração.",
            )
        )
    moonraker_errors = _filtered_log_lines(moonraker_log, ["traceback", "exception"])
    if moonraker_errors:
        findings.append(
            AuditFinding(
                id="recent_moonraker_severe_log",
                title="Moonraker tem erro severo recente nos logs filtrados",
                category="logs",
                classification="precisa_confirmacao",
                severity="warning",
                detail="; ".join(moonraker_errors[:5]),
                safe_action="Abrir trecho completo do moonraker.log antes de alterar serviços.",
            )
        )


def _filtered_log_lines(content: str, needles: list[str]) -> list[str]:
    result = []
    for line in content.splitlines():
        lowered = line.lower()
        if any(needle in lowered for needle in needles):
            result.append(line.strip())
    return result


def _match_text(content: str, pattern: str) -> str | None:
    match = re.search(pattern, content)
    return match.group(1) if match else None


def _match_int(content: str, pattern: str, flags: int = 0) -> int | None:
    match = re.search(pattern, content, flags=flags)
    return int(match.group(1)) if match else None


def _one_line(content: str) -> str:
    return " | ".join(line.strip() for line in content.splitlines() if line.strip())[:500]


def _non_empty_line_count(content: str) -> int:
    return len([line for line in content.splitlines() if line.strip()])
