import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.database import connect_database


SnapshotType = Literal["moonraker_status", "host_audit", "manual"]
DiffSeverity = Literal["info", "monitorar", "risco", "bloqueio"]


class SnapshotRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    created_at: str
    snapshot_type: str
    summary: dict[str, Any]


class SnapshotDetail(SnapshotRecord):
    payload: dict[str, Any]


class SnapshotDiffItem(BaseModel):
    field: str
    title: str
    severity: DiffSeverity
    before: Any
    after: Any
    detail: str


class SnapshotDiff(BaseModel):
    printer_id: int
    from_snapshot_id: int
    to_snapshot_id: int
    summary: str
    highest_severity: DiffSeverity
    changes: list[SnapshotDiffItem]


@dataclass(frozen=True)
class SnapshotRepository:
    database_path: Path

    def create_snapshot(
        self,
        printer_id: int,
        snapshot_type: SnapshotType,
        payload: dict[str, Any],
    ) -> SnapshotDetail:
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO printer_snapshots (printer_id, snapshot_type, payload_json)
                VALUES (?, ?, ?)
                """,
                (printer_id, snapshot_type, payload_json),
            )
            snapshot_id = int(cursor.lastrowid)
        snapshot = self.get_snapshot(snapshot_id)
        if snapshot is None:
            raise RuntimeError("snapshot was not persisted")
        return snapshot

    def list_snapshots(self, printer_id: int, limit: int = 20) -> list[SnapshotRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, created_at, snapshot_type, payload_json
                FROM printer_snapshots
                WHERE printer_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, limit),
            ).fetchall()
        return [_record_from_row(row, include_payload=False) for row in rows]

    def get_snapshot(self, snapshot_id: int) -> SnapshotDetail | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, created_at, snapshot_type, payload_json
                FROM printer_snapshots
                WHERE id = ?
                """,
                (snapshot_id,),
            ).fetchone()
        return _record_from_row(row, include_payload=True) if row else None

    def diff_snapshots(
        self,
        printer_id: int,
        from_snapshot_id: int,
        to_snapshot_id: int,
    ) -> SnapshotDiff | None:
        from_snapshot = self.get_snapshot(from_snapshot_id)
        to_snapshot = self.get_snapshot(to_snapshot_id)
        if (
            from_snapshot is None
            or to_snapshot is None
            or from_snapshot.printer_id != printer_id
            or to_snapshot.printer_id != printer_id
        ):
            return None
        return build_snapshot_diff(from_snapshot, to_snapshot)


def build_moonraker_snapshot_payload(
    printer_id: int,
    moonraker_url: str,
    printer_info: dict[str, Any],
    server_info: dict[str, Any],
    update_status: dict[str, Any],
    system_info: dict[str, Any],
    proc_stats: dict[str, Any],
) -> dict[str, Any]:
    return {
        "source": "moonraker",
        "safe_mode": "read_only",
        "printer_id": printer_id,
        "moonraker_url": moonraker_url,
        "printer_info": printer_info,
        "server_info": server_info,
        "update_status": update_status,
        "system_info": system_info,
        "proc_stats": proc_stats,
    }


def summarize_snapshot(snapshot_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    if snapshot_type == "moonraker_status":
        printer_info = payload.get("printer_info") if isinstance(payload.get("printer_info"), dict) else {}
        server_info = payload.get("server_info") if isinstance(payload.get("server_info"), dict) else {}
        update_status = payload.get("update_status") if isinstance(payload.get("update_status"), dict) else {}
        version_info = update_status.get("version_info") if isinstance(update_status.get("version_info"), dict) else {}
        dirty_repos = [
            name
            for name, repo in version_info.items()
            if isinstance(repo, dict) and repo.get("is_dirty") is True
        ]
        return {
            "klipper_state": printer_info.get("state"),
            "klipper_version": printer_info.get("software_version"),
            "moonraker_version": server_info.get("moonraker_version"),
            "failed_components": server_info.get("failed_components") or [],
            "warnings": server_info.get("warnings") or [],
            "dirty_repos": dirty_repos,
        }
    return {"keys": sorted(payload.keys())}


def build_snapshot_diff(from_snapshot: SnapshotDetail, to_snapshot: SnapshotDetail) -> SnapshotDiff:
    changes: list[SnapshotDiffItem] = []
    before = _extract_comparable_values(from_snapshot)
    after = _extract_comparable_values(to_snapshot)

    _compare_value(
        changes,
        "klipper_state",
        "Estado do Klipper",
        before,
        after,
        severity_when_changed="bloqueio" if after.get("klipper_state") != "ready" else "monitorar",
    )
    _compare_value(changes, "klipper_version", "Versão do Klipper", before, after, "monitorar")
    _compare_value(changes, "moonraker_version", "Versão do Moonraker", before, after, "monitorar")
    _compare_list(changes, "failed_components", "Componentes Moonraker com falha", before, after, "bloqueio")
    _compare_list(changes, "warnings", "Warnings Moonraker", before, after, "monitorar")
    _compare_list(changes, "dirty_repos", "Repos dirty", before, after, "risco")
    _compare_value(changes, "update_versions", "Versões do Update Manager", before, after, "info")
    _compare_cpu_temp(changes, before.get("cpu_temp"), after.get("cpu_temp"))

    highest = _highest_severity(changes)
    return SnapshotDiff(
        printer_id=from_snapshot.printer_id,
        from_snapshot_id=from_snapshot.id,
        to_snapshot_id=to_snapshot.id,
        summary=_diff_summary(highest, changes),
        highest_severity=highest,
        changes=changes,
    )


def _extract_comparable_values(snapshot: SnapshotDetail) -> dict[str, Any]:
    payload = snapshot.payload
    printer_info = payload.get("printer_info") if isinstance(payload.get("printer_info"), dict) else {}
    server_info = payload.get("server_info") if isinstance(payload.get("server_info"), dict) else {}
    update_status = payload.get("update_status") if isinstance(payload.get("update_status"), dict) else {}
    proc_stats = payload.get("proc_stats") if isinstance(payload.get("proc_stats"), dict) else {}
    version_info = update_status.get("version_info") if isinstance(update_status.get("version_info"), dict) else {}
    return {
        "klipper_state": printer_info.get("state"),
        "klipper_version": printer_info.get("software_version"),
        "moonraker_version": server_info.get("moonraker_version"),
        "failed_components": sorted(server_info.get("failed_components") or []),
        "warnings": sorted(server_info.get("warnings") or []),
        "dirty_repos": sorted(
            name
            for name, repo in version_info.items()
            if isinstance(repo, dict) and repo.get("is_dirty") is True
        ),
        "update_versions": _extract_update_versions(version_info),
        "cpu_temp": proc_stats.get("cpu_temp"),
    }


def _extract_update_versions(version_info: dict[str, Any]) -> dict[str, str | None]:
    tracked = [
        "klipper",
        "moonraker",
        "mainsail",
        "mainsail-config",
        "klipper-toolchanger-easy",
        "adaptive_meshing_purging",
        "led_effect",
    ]
    versions: dict[str, str | None] = {}
    for name in tracked:
        repo = version_info.get(name)
        if isinstance(repo, dict):
            versions[name] = repo.get("full_version_string") or repo.get("version")
    return versions


def _compare_value(
    changes: list[SnapshotDiffItem],
    field: str,
    title: str,
    before: dict[str, Any],
    after: dict[str, Any],
    severity_when_changed: DiffSeverity,
) -> None:
    if before.get(field) == after.get(field):
        return
    changes.append(
        SnapshotDiffItem(
            field=field,
            title=title,
            severity=severity_when_changed,
            before=before.get(field),
            after=after.get(field),
            detail=f"{title} mudou.",
        )
    )


def _compare_list(
    changes: list[SnapshotDiffItem],
    field: str,
    title: str,
    before: dict[str, Any],
    after: dict[str, Any],
    severity_when_changed: DiffSeverity,
) -> None:
    before_list = before.get(field) or []
    after_list = after.get(field) or []
    if before_list == after_list:
        return
    changes.append(
        SnapshotDiffItem(
            field=field,
            title=title,
            severity=severity_when_changed,
            before=before_list,
            after=after_list,
            detail=f"{title} mudou.",
        )
    )


def _compare_cpu_temp(changes: list[SnapshotDiffItem], before: Any, after: Any) -> None:
    if not isinstance(before, int | float) or not isinstance(after, int | float):
        return
    delta = after - before
    if abs(delta) < 10:
        return
    changes.append(
        SnapshotDiffItem(
            field="cpu_temp",
            title="Temperatura do host",
            severity="monitorar" if after < 75 else "risco",
            before=before,
            after=after,
            detail=f"Temperatura do host mudou {delta:.1f}C.",
        )
    )


def _highest_severity(changes: list[SnapshotDiffItem]) -> DiffSeverity:
    order: dict[DiffSeverity, int] = {"info": 0, "monitorar": 1, "risco": 2, "bloqueio": 3}
    if not changes:
        return "info"
    return max((change.severity for change in changes), key=lambda severity: order[severity])


def _diff_summary(highest: DiffSeverity, changes: list[SnapshotDiffItem]) -> str:
    if not changes:
        return "Sem mudanças relevantes entre os snapshots."
    if highest == "bloqueio":
        return "Há mudança crítica. Revisar antes de imprimir."
    if highest == "risco":
        return "Há mudança de risco. Revisar antes de continuar."
    if highest == "monitorar":
        return "Há mudanças para monitorar."
    return "Apenas mudanças informativas."


def _record_from_row(row, include_payload: bool) -> SnapshotRecord | SnapshotDetail:
    payload = json.loads(row["payload_json"])
    summary = summarize_snapshot(str(row["snapshot_type"]), payload)
    base = {
        "id": int(row["id"]),
        "printer_id": int(row["printer_id"]),
        "created_at": str(row["created_at"]),
        "snapshot_type": str(row["snapshot_type"]),
        "summary": summary,
    }
    if include_payload:
        return SnapshotDetail(**base, payload=payload)
    return SnapshotRecord(**base)
