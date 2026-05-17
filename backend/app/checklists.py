from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ChecklistItem:
    key: str
    title: str
    ok: bool
    severity: str
    detail: str


def build_post_update_checklist(
    printer_info: dict[str, Any],
    server_info: dict[str, Any],
    update_status: dict[str, Any],
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
        ),
        ChecklistItem(
            key="moonraker_connected",
            title="Moonraker conectado ao Klipper",
            ok=server_info.get("klippy_connected") is True and server_info.get("klippy_state") == "ready",
            severity="blocker",
            detail=f"connected={server_info.get('klippy_connected')} state={server_info.get('klippy_state')}",
        ),
        ChecklistItem(
            key="moonraker_components",
            title="Componentes Moonraker sem falha",
            ok=not server_info.get("failed_components") and not server_info.get("warnings"),
            severity="warning",
            detail=f"failed={server_info.get('failed_components') or []} warnings={server_info.get('warnings') or []}",
        ),
        ChecklistItem(
            key="update_manager",
            title="Update Manager sem avisos nos repositórios principais",
            ok=not repo_warnings,
            severity="warning",
            detail="; ".join(repo_warnings) if repo_warnings else "sem warnings/anomalias detectadas",
        ),
    ]

    can_print = all(item.ok or item.severity != "blocker" for item in items)
    return {
        "can_print": can_print,
        "summary": "OK para imprimir" if can_print else "Não imprima ainda",
        "items": [item.__dict__ for item in items],
    }
