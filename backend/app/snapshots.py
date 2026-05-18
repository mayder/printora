import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict

from app.database import connect_database


SnapshotType = Literal["moonraker_status", "host_audit", "manual"]


class SnapshotRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    created_at: str
    snapshot_type: str
    summary: dict[str, Any]


class SnapshotDetail(SnapshotRecord):
    payload: dict[str, Any]


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
