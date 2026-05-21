from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChecklistItem:
    key: str
    title: str
    ok: bool
    severity: str
    detail: str
    status: str
    source: str


def build_post_update_checklist(
    printer_info: dict[str, Any],
    server_info: dict[str, Any],
    update_status: dict[str, Any],
    *,
    data_state: str = "live",
    source: str = "moonraker",
    error: str | None = None,
) -> dict[str, Any]:
    version_info = update_status.get("version_info", {})
    tracked_repos = [
        "klipper",
        "moonraker",
        "mainsail",
        "mainsail-config",
        "klipper-toolchanger-easy",
        "adaptive_meshing_purging",
        "led_effect",
    ]

    repo_warnings: list[str] = []
    for name in tracked_repos:
        repo = version_info.get(name)
        if not isinstance(repo, dict):
            continue
        warnings = repo.get("warnings") or []
        anomalies = repo.get("anomalies") or []
        dirty = repo.get("is_dirty")
        behind = repo.get("commits_behind_count")
        if warnings or anomalies or dirty or (isinstance(behind, int) and behind > 0):
            repo_warnings.append(
                f"{name}: dirty={dirty} behind={behind} warnings={warnings} anomalies={anomalies}"
            )

    items = [
        ChecklistItem(
            key="klipper_ready",
            title="Klipper ready",
            ok=printer_info.get("state") == "ready",
            severity="blocker",
            detail=str(printer_info.get("state_message") or printer_info.get("state") or "unknown"),
            status=_item_status(printer_info.get("state") == "ready", data_state, "blocker"),
            source=source,
        ),
        ChecklistItem(
            key="moonraker_connected",
            title="Moonraker conectado ao Klipper",
            ok=server_info.get("klippy_connected") is True and server_info.get("klippy_state") == "ready",
            severity="blocker",
            detail=f"connected={server_info.get('klippy_connected')} state={server_info.get('klippy_state')}",
            status=_item_status(server_info.get("klippy_connected") is True and server_info.get("klippy_state") == "ready", data_state, "blocker"),
            source=source,
        ),
        ChecklistItem(
            key="moonraker_components",
            title="Componentes Moonraker sem falha",
            ok=not server_info.get("failed_components") and not server_info.get("warnings"),
            severity="warning",
            detail=f"failed={server_info.get('failed_components') or []} warnings={server_info.get('warnings') or []}",
            status=_item_status(not server_info.get("failed_components") and not server_info.get("warnings"), data_state, "warning"),
            source=source,
        ),
        ChecklistItem(
            key="update_manager",
            title="Update Manager sem avisos nos repositórios principais",
            ok=not repo_warnings,
            severity="warning",
            detail="; ".join(repo_warnings) if repo_warnings else "sem warnings/anomalias detectadas",
            status=_item_status(not repo_warnings, data_state, "warning"),
            source=source,
        ),
        ChecklistItem(
            key="manual_smoke",
            title="Smoke test manual pós-update",
            ok=False,
            severity="manual",
            detail="Confirmar home, aquecimento, fans, primeira camada e ausência de erros no console antes de imprimir.",
            status="manual",
            source="operador",
        ),
    ]

    can_print = data_state == "live" and all(item.ok or item.severity != "blocker" for item in items)
    return {
        "can_print": can_print,
        "data_state": data_state,
        "source": source,
        "error": error,
        "summary": _summary(can_print, data_state),
        "items": [item.__dict__ for item in items],
    }


def build_unavailable_post_update_checklist(*, data_state: str, source: str, error: str) -> dict[str, Any]:
    return {
        "can_print": False,
        "data_state": data_state,
        "source": source,
        "error": error,
        "summary": _summary(False, data_state),
        "items": [
            ChecklistItem(
                key="moonraker_read",
                title="Leitura Moonraker",
                ok=False,
                severity="blocker",
                detail=error,
                status="blocked" if data_state == "offline" else "unknown",
                source=source,
            ).__dict__,
            ChecklistItem(
                key="manual_smoke",
                title="Smoke test manual pós-update",
                ok=False,
                severity="manual",
                detail="Checklist técnico não validável sem leitura ao vivo ou snapshot. Não considere a impressora pronta.",
                status="manual",
                source="operador",
            ).__dict__,
        ],
    }


def _item_status(ok: bool, data_state: str, severity: str) -> str:
    if ok:
        return "ok"
    if data_state != "live":
        return "unknown"
    if severity == "blocker":
        return "blocked"
    return "warning"


def _summary(can_print: bool, data_state: str) -> str:
    if can_print:
        return "Seguro imprimir após smoke manual"
    if data_state == "last_snapshot":
        return "Não imprima ainda: usando último snapshot"
    if data_state == "offline":
        return "Não imprima ainda: Moonraker offline"
    if data_state == "no_data":
        return "Não imprima ainda: sem dados para validar"
    return "Não imprima ainda"
