from dataclasses import dataclass
from typing import Any, Literal


Classification = Literal["corrigir_agora", "monitorar", "ignorar", "precisa_confirmacao"]
Severity = Literal["blocker", "warning", "info"]


TRACKED_REPOSITORIES = [
    "klipper",
    "moonraker",
    "mainsail",
    "mainsail-config",
    "klipper-toolchanger-easy",
    "adaptive_meshing_purging",
    "led_effect",
]


@dataclass(frozen=True)
class AuditFinding:
    id: str
    title: str
    category: str
    classification: Classification
    severity: Severity
    detail: str
    safe_action: str


def build_read_only_audit(
    printer_info: dict[str, Any],
    server_info: dict[str, Any],
    update_status: dict[str, Any],
    system_info: dict[str, Any] | None = None,
    proc_stats: dict[str, Any] | None = None,
    *,
    data_state: str = "live",
    source: str = "moonraker",
    error: str | None = None,
) -> dict[str, Any]:
    findings: list[AuditFinding] = []

    _audit_klipper(findings, printer_info)
    _audit_moonraker(findings, server_info)
    _audit_update_manager(findings, update_status)
    _audit_system(findings, system_info or {}, proc_stats or {})

    if not findings:
        findings.append(
            AuditFinding(
                id="no_critical_findings",
                title="Nenhum problema crítico detectado",
                category="geral",
                classification="ignorar",
                severity="info",
                detail="A auditoria somente leitura não encontrou bloqueios nos dados disponíveis.",
                safe_action="Continuar monitorando após updates, manutenções e primeiras impressões.",
            )
        )

    return {
        "safe_mode": "read_only",
        "data_state": data_state,
        "source": source,
        "error": error,
        "summary": _build_summary(findings),
        "counts": _count_by_classification(findings),
        "findings": [finding.__dict__ for finding in findings],
    }


def _audit_klipper(findings: list[AuditFinding], printer_info: dict[str, Any]) -> None:
    state = printer_info.get("state")
    if state != "ready":
        findings.append(
            AuditFinding(
                id="klipper_not_ready",
                title="Klipper não está ready",
                category="klipper",
                classification="corrigir_agora",
                severity="blocker",
                detail=str(printer_info.get("state_message") or state or "estado desconhecido"),
                safe_action="Não imprimir. Abrir logs do Klipper e corrigir a causa antes de reiniciar.",
            )
        )

    software_version = str(printer_info.get("software_version") or "")
    if software_version.endswith("-dirty"):
        findings.append(
            AuditFinding(
                id="klipper_dirty_version",
                title="Klipper aparece como dirty",
                category="klipper",
                classification="monitorar",
                severity="warning",
                detail=f"software_version={software_version}",
                safe_action=(
                    "Comparar com o Update Manager. Se o repo Klipper estiver limpo, "
                    "pode ser efeito esperado de módulos externos em klippy/extras."
                ),
            )
        )


def _audit_moonraker(findings: list[AuditFinding], server_info: dict[str, Any]) -> None:
    if server_info.get("klippy_connected") is not True or server_info.get("klippy_state") != "ready":
        findings.append(
            AuditFinding(
                id="moonraker_not_connected",
                title="Moonraker não está conectado ao Klipper ready",
                category="moonraker",
                classification="corrigir_agora",
                severity="blocker",
                detail=(
                    f"klippy_connected={server_info.get('klippy_connected')} "
                    f"klippy_state={server_info.get('klippy_state')}"
                ),
                safe_action="Não imprimir. Validar Klipper, Moonraker e comunicação entre os serviços.",
            )
        )

    failed_components = server_info.get("failed_components") or []
    if failed_components:
        findings.append(
            AuditFinding(
                id="moonraker_failed_components",
                title="Moonraker tem componentes com falha",
                category="moonraker",
                classification="corrigir_agora",
                severity="blocker",
                detail=", ".join(map(str, failed_components)),
                safe_action="Verificar moonraker.log antes de qualquer update ou impressão nova.",
            )
        )

    warnings = server_info.get("warnings") or []
    if warnings:
        findings.append(
            AuditFinding(
                id="moonraker_warnings",
                title="Moonraker reportou warnings",
                category="moonraker",
                classification="monitorar",
                severity="warning",
                detail="; ".join(map(str, warnings)),
                safe_action="Revisar warnings e resolver antes de mudanças maiores no ambiente.",
            )
        )


def _audit_update_manager(findings: list[AuditFinding], update_status: dict[str, Any]) -> None:
    version_info = update_status.get("version_info", {})
    if not isinstance(version_info, dict) or not version_info:
        findings.append(
            AuditFinding(
                id="update_manager_unavailable",
                title="Update Manager sem dados de versão",
                category="update_manager",
                classification="precisa_confirmacao",
                severity="warning",
                detail="A resposta não trouxe version_info.",
                safe_action="Confirmar se o componente update_manager está carregado no Moonraker.",
            )
        )
        return

    for name in TRACKED_REPOSITORIES:
        repo = version_info.get(name)
        if not isinstance(repo, dict):
            continue

        warnings = repo.get("warnings") or []
        anomalies = repo.get("anomalies") or []
        dirty = repo.get("is_dirty")
        behind = repo.get("commits_behind_count")
        if warnings or anomalies or dirty or (isinstance(behind, int) and behind > 0):
            findings.append(
                AuditFinding(
                    id=f"repo_{name}_needs_attention",
                    title=f"Repositório {name} precisa atenção",
                    category="update_manager",
                    classification="monitorar",
                    severity="warning",
                    detail=(
                        f"dirty={dirty} behind={behind} "
                        f"warnings={warnings} anomalies={anomalies}"
                    ),
                    safe_action="Não atualizar durante impressão. Revisar status Git e logs antes de corrigir.",
                )
            )


def _audit_system(
    findings: list[AuditFinding],
    system_info: dict[str, Any],
    proc_stats: dict[str, Any],
) -> None:
    cpu_temp = _extract_number(proc_stats, ["cpu_temp", "temperature"])
    if cpu_temp is not None and cpu_temp >= 75:
        findings.append(
            AuditFinding(
                id="host_temperature_high",
                title="Temperatura do host alta",
                category="sistema",
                classification="monitorar",
                severity="warning",
                detail=f"cpu_temp={cpu_temp:.1f}C",
                safe_action="Verificar ventilação da Raspberry Pi e carga do sistema.",
            )
        )

    available_bytes = _find_nested_number(system_info, ["available", "free"])
    if available_bytes is not None and available_bytes < 1_000_000_000:
        findings.append(
            AuditFinding(
                id="disk_space_low",
                title="Espaço livre baixo",
                category="sistema",
                classification="monitorar",
                severity="warning",
                detail=f"available_bytes={int(available_bytes)}",
                safe_action="Planejar limpeza de logs, backups antigos e archives com confirmação.",
            )
        )


def _extract_number(data: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, int | float):
            return float(value)
    return None


def _find_nested_number(data: Any, preferred_keys: list[str]) -> float | None:
    if isinstance(data, dict):
        for key in preferred_keys:
            value = data.get(key)
            if isinstance(value, int | float):
                return float(value)
        for value in data.values():
            found = _find_nested_number(value, preferred_keys)
            if found is not None:
                return found
    elif isinstance(data, list):
        for value in data:
            found = _find_nested_number(value, preferred_keys)
            if found is not None:
                return found
    return None


def _count_by_classification(findings: list[AuditFinding]) -> dict[str, int]:
    counts = {
        "corrigir_agora": 0,
        "monitorar": 0,
        "ignorar": 0,
        "precisa_confirmacao": 0,
    }
    for finding in findings:
        counts[finding.classification] += 1
    return counts


def _build_summary(findings: list[AuditFinding]) -> str:
    if any(finding.severity == "blocker" for finding in findings):
        return "Há bloqueios. Não inicie nova impressão antes de corrigir."
    if any(finding.classification in {"monitorar", "precisa_confirmacao"} for finding in findings):
        return "Sem bloqueio crítico, mas há itens para revisar."
    return "Ambiente sem problemas críticos nos dados disponíveis."
