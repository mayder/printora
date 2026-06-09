from __future__ import annotations

import json
from pathlib import Path
import hashlib
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agent_pairing import AgentRecord
from app.database import connect_database


AGENT_UPDATE_MANIFEST_VERSION = 1
AGENT_UPDATE_PROTOCOL_VERSION = 1
AGENT_CURRENT_VERSION = "0.1.19"
AGENT_MANIFEST_PATH = Path(__file__).resolve().parent / "data" / "agent_update_manifest.json"

AgentUpdateStatus = Literal["available", "blocked", "downloaded", "applied", "rolled_back", "failed", "skipped"]


class AgentReleaseAsset(BaseModel):
    platform: str
    version: str
    url: str = ""
    sha256: str = ""
    signature: str | None = None
    protocol_min: int = AGENT_UPDATE_PROTOCOL_VERSION
    protocol_max: int = AGENT_UPDATE_PROTOCOL_VERSION


class AgentUpdateManifest(BaseModel):
    manifest_version: int = AGENT_UPDATE_MANIFEST_VERSION
    minimum_version: str = AGENT_CURRENT_VERSION
    recommended_version: str = AGENT_CURRENT_VERSION
    blocked_versions: list[str] = Field(default_factory=list)
    protocol_version: int = AGENT_UPDATE_PROTOCOL_VERSION
    protocol_min: int = AGENT_UPDATE_PROTOCOL_VERSION
    protocol_max: int = AGENT_UPDATE_PROTOCOL_VERSION
    auto_update: bool = True
    releases: list[AgentReleaseAsset] = Field(default_factory=list)


class AgentUpdateReportRequest(BaseModel):
    status: AgentUpdateStatus
    current_version: str = Field(max_length=80)
    target_version: str | None = Field(default=None, max_length=80)
    platform: str | None = Field(default=None, max_length=120)
    detail: str | None = Field(default=None, max_length=500)


class AgentUpdateHistoryRecord(BaseModel):
    id: int
    printer_id: int
    agent_id: int | None
    event_type: str
    status: str
    detail: str | None
    created_at: str


class AgentUpdateRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def report(self, agent: AgentRecord, payload: AgentUpdateReportRequest) -> AgentUpdateHistoryRecord:
        detail = {
            "current_version": payload.current_version,
            "target_version": payload.target_version,
            "platform": payload.platform,
            "detail": payload.detail,
        }
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO printer_agent_events (printer_id, agent_id, event_type, status, detail)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    agent.printer_id,
                    agent.id,
                    "agent_update",
                    payload.status,
                    _safe_detail(detail),
                ),
            )
            row = connection.execute(
                """
                SELECT id, printer_id, agent_id, event_type, status, detail, created_at
                FROM printer_agent_events
                WHERE id = ?
                """,
                (int(cursor.lastrowid),),
            ).fetchone()
        return _history_from_row(row)

    def history(self, printer_id: int, limit: int = 50) -> list[AgentUpdateHistoryRecord]:
        clean_limit = max(1, min(limit, 100))
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, agent_id, event_type, status, detail, created_at
                FROM printer_agent_events
                WHERE printer_id = ? AND event_type = 'agent_update'
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, clean_limit),
            ).fetchall()
        return [_history_from_row(row) for row in rows]


def load_agent_update_manifest(public_base_url: str | None = None) -> AgentUpdateManifest:
    if not AGENT_MANIFEST_PATH.exists():
        return _default_manifest(public_base_url)
    data = json.loads(AGENT_MANIFEST_PATH.read_text())
    return _with_local_release_assets(AgentUpdateManifest.model_validate(data), public_base_url)


def _default_manifest(public_base_url: str | None = None) -> AgentUpdateManifest:
    return _with_local_release_assets(AgentUpdateManifest(
        releases=[
            AgentReleaseAsset(platform="linux/amd64", version=AGENT_CURRENT_VERSION),
            AgentReleaseAsset(platform="linux/arm64", version=AGENT_CURRENT_VERSION),
            AgentReleaseAsset(platform="linux/arm", version=AGENT_CURRENT_VERSION),
        ]
    ), public_base_url)


def _with_local_release_assets(manifest: AgentUpdateManifest, public_base_url: str | None) -> AgentUpdateManifest:
    release_dir = Path(__file__).resolve().parent / "data" / "agent_releases"
    local_files = {
        "linux/arm64": ("linux-arm64", "printora-agent-linux-arm64"),
    }
    releases: list[AgentReleaseAsset] = []
    for release in manifest.releases:
        local = local_files.get(release.platform)
        if local is None:
            releases.append(release)
            continue
        route_platform, filename = local
        path = release_dir / filename
        if not path.exists() or not path.is_file():
            releases.append(release)
            continue
        url = release.url
        if public_base_url:
            url = f"{public_base_url.rstrip('/')}/api/agent/update/releases/{route_platform}"
        releases.append(release.model_copy(update={"url": url, "sha256": _sha256_file(path)}))
    return manifest.model_copy(update={"releases": releases})


def _sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def _history_from_row(row) -> AgentUpdateHistoryRecord:
    return AgentUpdateHistoryRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        agent_id=int(row["agent_id"]) if row["agent_id"] is not None else None,
        event_type=str(row["event_type"]),
        status=str(row["status"]),
        detail=row["detail"],
        created_at=str(row["created_at"]),
    )


def _safe_detail(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return text[:500]
