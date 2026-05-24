from dataclasses import dataclass
from typing import Any, Literal

from app.audit import TRACKED_REPOSITORIES
from app.snapshots import SnapshotDiff, SnapshotRecord


HealthDecision = Literal["ok_para_imprimir", "monitorar", "nao_imprimir"]
HealthSeverity = Literal["ok", "info", "warning", "blocker"]


@dataclass(frozen=True)
class HealthItem:
    key: str
    title: str
    ok: bool
    severity: HealthSeverity
    detail: str
    action: str


def build_printer_health(
    printer_info: dict[str, Any],
    server_info: dict[str, Any],
    update_status: dict[str, Any],
    system_info: dict[str, Any],
    proc_stats: dict[str, Any],
    snapshots: list[SnapshotRecord],
    latest_diff: SnapshotDiff | None = None,
    *,
    data_state: str = "live",
    source: str = "moonraker",
    api_latency_ms: float | None = None,
    error: str | None = None,
) -> dict[str, Any]:
    items: list[HealthItem] = []

    _check_data_state(items, data_state, source, error)
    _check_klipper(items, printer_info)
    _check_moonraker(items, server_info)
    _check_update_manager(items, update_status)
    _check_host_metrics(items, system_info, proc_stats)
    _check_api_latency(items, api_latency_ms)
    _check_snapshots(items, snapshots, latest_diff)

    decision = _decision(items)
    return {
        "safe_mode": "read_only",
        "connected": data_state == "live",
        "data_state": data_state,
        "source": source,
        "error": error,
        "decision": decision,
        "summary": _summary(decision),
        "metrics": _metrics(
            printer_info,
            server_info,
            system_info,
            proc_stats,
            snapshots,
            latest_diff,
            api_latency_ms,
            data_state,
        ),
        "counts": _counts(items),
        "items": [item.__dict__ for item in items],
    }


def build_unreachable_health(moonraker_url: str, error: str) -> dict[str, Any]:
    item = HealthItem(
        key="moonraker_unreachable",
        title="Moonraker indisponível",
        ok=False,
        severity="blocker",
        detail=error,
        action="Não imprimir por este app. Validar URL, rede e serviço Moonraker.",
    )
    return {
        "safe_mode": "read_only",
        "connected": False,
        "data_state": "offline",
        "source": moonraker_url,
        "error": error,
        "moonraker_url": moonraker_url,
        "decision": "nao_imprimir",
        "summary": "Não imprima ainda",
        "metrics": {},
        "counts": _counts([item]),
        "items": [item.__dict__],
    }


def _check_data_state(items: list[HealthItem], data_state: str, source: str, error: str | None) -> None:
    if data_state == "live":
        items.append(
            HealthItem(
                key="data_state",
                title="Origem dos dados",
                ok=True,
                severity="ok",
                detail=f"Leitura ao vivo de {source}.",
                action="Sem ação.",
            )
        )
        return

    detail = f"Usando {source}."
    if error:
        detail = f"{detail} Falha ao ler Moonraker ao vivo: {error}"
    items.append(
        HealthItem(
            key="data_state",
            title="Origem dos dados",
            ok=False,
            severity="blocker",
            detail=detail,
            action="Não considerar a impressora pronta sem uma leitura ao vivo.",
        )
    )


def _check_klipper(items: list[HealthItem], printer_info: dict[str, Any]) -> None:
    state = printer_info.get("state")
    ready = state == "ready"
    items.append(
        HealthItem(
            key="klipper_ready",
            title="Klipper ready",
            ok=ready,
            severity="ok" if ready else "blocker",
            detail=str(printer_info.get("state_message") or state or "estado desconhecido"),
            action="Não imprimir até o Klipper voltar para ready." if not ready else "Sem ação.",
        )
    )


def _check_moonraker(items: list[HealthItem], server_info: dict[str, Any]) -> None:
    connected = server_info.get("klippy_connected") is True and server_info.get("klippy_state") == "ready"
    items.append(
        HealthItem(
            key="moonraker_connected",
            title="Moonraker conectado ao Klipper",
            ok=connected,
            severity="ok" if connected else "blocker",
            detail=f"connected={server_info.get('klippy_connected')} state={server_info.get('klippy_state')}",
            action="Validar Klipper e Moonraker antes de imprimir." if not connected else "Sem ação.",
        )
    )

    failed_components = server_info.get("failed_components") or []
    warnings = server_info.get("warnings") or []
    clean = not failed_components and not warnings
    items.append(
        HealthItem(
            key="moonraker_components",
            title="Componentes Moonraker",
            ok=clean,
            severity="ok" if clean else "blocker" if failed_components else "warning",
            detail=f"failed={failed_components} warnings={warnings}",
            action="Revisar moonraker.log antes de imprimir." if not clean else "Sem ação.",
        )
    )


def _check_update_manager(items: list[HealthItem], update_status: dict[str, Any]) -> None:
    version_info = update_status.get("version_info", {})
    if not isinstance(version_info, dict) or not version_info:
        items.append(
            HealthItem(
                key="update_manager",
                title="Update Manager",
                ok=False,
                severity="warning",
                detail="version_info ausente.",
                action="Confirmar se o Update Manager está carregado no Moonraker.",
            )
        )
        return

    problems: list[str] = []
    for name in TRACKED_REPOSITORIES:
        repo = version_info.get(name)
        if not isinstance(repo, dict):
            continue
        warnings = repo.get("warnings") or []
        anomalies = repo.get("anomalies") or []
        dirty = repo.get("is_dirty")
        behind = repo.get("commits_behind_count")
        if warnings or anomalies or dirty or (isinstance(behind, int) and behind > 0):
            problems.append(f"{name}: dirty={dirty} behind={behind} warnings={warnings} anomalies={anomalies}")

    items.append(
        HealthItem(
            key="update_manager",
            title="Update Manager",
            ok=not problems,
            severity="ok" if not problems else "warning",
            detail="sem warnings/anomalias detectadas" if not problems else "; ".join(problems),
            action="Não atualizar durante impressão. Revisar repositórios antes de mudanças maiores."
            if problems
            else "Sem ação.",
        )
    )


def _check_host_metrics(
    items: list[HealthItem],
    system_info: dict[str, Any],
    proc_stats: dict[str, Any],
) -> None:
    cpu_temp = _extract_number(proc_stats, ["cpu_temp", "temperature"])
    if cpu_temp is not None:
        severity: HealthSeverity = "ok"
        ok = True
        action = "Sem ação."
        if cpu_temp >= 80:
            severity = "blocker"
            ok = False
            action = "Não iniciar nova impressão antes de melhorar a refrigeração do host."
        elif cpu_temp >= 70:
            severity = "warning"
            ok = False
            action = "Monitorar temperatura e ventilação da Raspberry Pi."
        items.append(
            HealthItem(
                key="host_temperature",
                title="Temperatura do host",
                ok=ok,
                severity=severity,
                detail=f"{cpu_temp:.1f}C",
                action=action,
            )
        )

    disk = _find_disk_values(system_info)
    if disk is not None:
        available_bytes, total_bytes = disk
    else:
        available_bytes, total_bytes = None, None
    if available_bytes is not None:
        low_space = available_bytes < 1_000_000_000
        items.append(
            HealthItem(
                key="disk_space",
                title="Espaço livre",
                ok=not low_space,
                severity="warning" if low_space else "ok",
                detail=f"{available_bytes / 1_000_000_000:.2f} GB disponíveis",
                action="Planejar limpeza de logs/backups antigos." if low_space else "Sem ação.",
            )
        )
    elif total_bytes is not None:
        items.append(
            HealthItem(
                key="disk_space",
                title="Armazenamento detectado",
                ok=True,
                severity="ok",
                detail=f"{total_bytes / 1_000_000_000:.2f} GB totais; espaço livre não reportado pelo Moonraker.",
                action="Validar espaço livre no host antes de updates ou backups grandes.",
            )
        )
    else:
        items.append(
            HealthItem(
                key="disk_space",
                title="Armazenamento",
                ok=True,
                severity="info",
                detail="Moonraker não reportou capacidade ou espaço livre do disco.",
                action="Validar espaço livre no host antes de updates ou backups grandes.",
            )
        )

    memory = _find_memory_values(proc_stats) or _find_memory_values(system_info)
    if memory is not None:
        available, total = memory
        usage_ratio = 1 - (available / total) if total > 0 else 0
        severity: HealthSeverity = "ok"
        ok = True
        action = "Sem ação."
        if usage_ratio >= 0.90:
            severity = "warning"
            ok = False
            action = "Monitorar processos do host antes de iniciar impressão longa."
        items.append(
            HealthItem(
                key="host_memory",
                title="Memória do host",
                ok=ok,
                severity=severity,
                detail=f"{available / 1_000_000_000:.2f} GB livres de {total / 1_000_000_000:.2f} GB",
                action=action,
            )
        )


def _check_api_latency(items: list[HealthItem], api_latency_ms: float | None) -> None:
    if api_latency_ms is None:
        return
    severity: HealthSeverity = "ok"
    ok = True
    action = "Sem ação."
    if api_latency_ms >= 5_000:
        severity = "warning"
        ok = False
        action = "Monitorar a rede do Printora. Isso afeta ações do app, não a impressão já controlada pelo Klipper na Raspberry."
    elif api_latency_ms >= 1_500:
        severity = "warning"
        ok = False
        action = "Monitorar a rede do Printora antes de ações longas pelo app."
    items.append(
        HealthItem(
            key="api_latency",
            title="Comunicação Printora ↔ Moonraker lenta",
            ok=ok,
            severity=severity,
            detail=f"{api_latency_ms:.0f} ms",
            action=action,
        )
    )


def _check_snapshots(
    items: list[HealthItem],
    snapshots: list[SnapshotRecord],
    latest_diff: SnapshotDiff | None,
) -> None:
    has_snapshot = bool(snapshots)
    items.append(
        HealthItem(
            key="snapshots",
            title="Snapshots recentes",
            ok=has_snapshot,
            severity="ok" if has_snapshot else "info",
            detail=f"{len(snapshots)} snapshots disponíveis",
            action="Capturar snapshot após update/manutenção." if not has_snapshot else "Sem ação.",
        )
    )

    if latest_diff is None:
        return

    severity_map: dict[str, HealthSeverity] = {
        "info": "ok",
        "monitorar": "warning",
        "risco": "warning",
        "bloqueio": "blocker",
    }
    severity = severity_map[latest_diff.highest_severity]
    items.append(
        HealthItem(
            key="latest_snapshot_diff",
            title="Última comparação de snapshots",
            ok=severity == "ok",
            severity=severity,
            detail=latest_diff.summary,
            action="Revisar mudanças antes de imprimir." if severity != "ok" else "Sem ação.",
        )
    )


def _metrics(
    printer_info: dict[str, Any],
    server_info: dict[str, Any],
    system_info: dict[str, Any],
    proc_stats: dict[str, Any],
    snapshots: list[SnapshotRecord],
    latest_diff: SnapshotDiff | None,
    api_latency_ms: float | None,
    data_state: str,
) -> dict[str, Any]:
    return {
        "data_state": data_state,
        "klipper_state": printer_info.get("state"),
        "klipper_version": printer_info.get("software_version"),
        "moonraker_version": server_info.get("moonraker_version"),
        "cpu_temp": _extract_number(proc_stats, ["cpu_temp", "temperature"]),
        "disk_available_bytes": (_find_disk_values(system_info) or (None, None))[0],
        "disk_total_bytes": (_find_disk_values(system_info) or (None, None))[1],
        "memory_available_bytes": (_find_memory_values(proc_stats) or _find_memory_values(system_info) or (None, None))[0],
        "memory_total_bytes": (_find_memory_values(proc_stats) or _find_memory_values(system_info) or (None, None))[1],
        "api_latency_ms": api_latency_ms,
        "snapshot_count": len(snapshots),
        "latest_snapshot_id": snapshots[0].id if snapshots else None,
        "latest_diff_severity": latest_diff.highest_severity if latest_diff else None,
    }


def _decision(items: list[HealthItem]) -> HealthDecision:
    if any(item.severity == "blocker" for item in items):
        return "nao_imprimir"
    if any(item.severity == "warning" for item in items):
        return "monitorar"
    return "ok_para_imprimir"


def _summary(decision: HealthDecision) -> str:
    if decision == "nao_imprimir":
        return "Não imprima ainda"
    if decision == "monitorar":
        return "Pode imprimir com atenção"
    return "OK para imprimir"


def _counts(items: list[HealthItem]) -> dict[str, int]:
    counts = {"ok": 0, "info": 0, "warning": 0, "blocker": 0}
    for item in items:
        counts[item.severity] += 1
    return counts


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


def _find_memory_values(data: Any) -> tuple[float, float] | None:
    if not isinstance(data, dict):
        return None
    candidates = [
        data.get("memory"),
        data.get("system_memory"),
        data.get("mem"),
        data,
    ]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        total = _first_number(candidate, ["total", "total_bytes", "MemTotal"])
        available = _first_number(candidate, ["available", "available_bytes", "free", "free_bytes", "MemAvailable"])
        used = _first_number(candidate, ["used", "used_bytes"])
        if total is not None and available is None and used is not None:
            available = total - used
        if total is not None and available is not None and total > 0:
            return _normalize_memory_bytes(float(max(0, available)), float(total), candidate)
    for value in data.values():
        found = _find_memory_values(value)
        if found is not None:
            return found
    return None


def _find_disk_values(data: Any) -> tuple[float | None, float | None] | None:
    if not isinstance(data, dict):
        return None
    candidates = [
        data.get("disk"),
        data.get("disk_usage"),
        data.get("sd_info"),
        data,
    ]
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        total = _first_number(candidate, ["total_bytes", "total", "capacity_bytes"])
        available = _first_number(candidate, ["available_bytes", "available", "free_bytes", "free"])
        used = _first_number(candidate, ["used_bytes", "used"])
        if total is not None and available is None and used is not None:
            available = total - used
        if total is not None and total <= 0:
            total = None
        if available is not None and available <= 0:
            available = None
        if total is not None or available is not None:
            return (float(max(0, available)) if available is not None else None, float(total) if total is not None else None)
    for value in data.values():
        found = _find_disk_values(value)
        if found is not None:
            return found
    return None


def _normalize_memory_bytes(available: float, total: float, payload: dict[str, Any]) -> tuple[float, float]:
    units = str(payload.get("memory_units") or payload.get("mem_units") or "").lower()
    if units in {"kb", "kib"} or total < 100_000_000:
        return available * 1024, total * 1024
    if units in {"mb", "mib"}:
        return available * 1024 * 1024, total * 1024 * 1024
    return available, total


def _first_number(data: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        value = data.get(key)
        if isinstance(value, int | float):
            return float(value)
    return None
