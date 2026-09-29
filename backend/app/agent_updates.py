from __future__ import annotations

import json
from pathlib import Path
import hashlib
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from app.agent_pairing import AgentRecord
from app.database import connect_database


AGENT_UPDATE_MANIFEST_VERSION = 1
AGENT_UPDATE_PROTOCOL_VERSION = 1
AGENT_CURRENT_VERSION = "0.1.36"
AGENT_RECOMMENDED_VERSION = "0.1.36"
AGENT_MANIFEST_PATH = Path(__file__).resolve().parent / "data" / "agent_update_manifest.json"
AGENT_SIGNATURE_ALGORITHM = "ed25519-sha256"
AGENT_SIGNING_KEY_ID = "sha256:e241d16ebb469da7436ff050a36212635557eab1322495a2c62e2ca6caf24cdc"

AgentUpdateStatus = Literal["available", "blocked", "downloaded", "applied", "rolled_back", "failed", "skipped"]


class AgentReleaseAsset(BaseModel):
    platform: Literal["linux/arm64"]
    version: str
    url: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    signature: str = Field(min_length=80)
    signature_scope: Literal["printora-agent-release-v1", "legacy-digest-only"]
    protocol_min: int = AGENT_UPDATE_PROTOCOL_VERSION
    protocol_max: int = AGENT_UPDATE_PROTOCOL_VERSION


class AgentUpdateManifest(BaseModel):
    manifest_version: int = AGENT_UPDATE_MANIFEST_VERSION
    minimum_version: str = "0.1.17"
    recommended_version: str = AGENT_RECOMMENDED_VERSION
    candidate_version: str | None = None
    blocked_versions: list[str] = Field(default_factory=list)
    protocol_version: int = AGENT_UPDATE_PROTOCOL_VERSION
    protocol_min: int = AGENT_UPDATE_PROTOCOL_VERSION
    protocol_max: int = AGENT_UPDATE_PROTOCOL_VERSION
    signature_algorithm: Literal["ed25519-sha256"] = AGENT_SIGNATURE_ALGORITHM
    signing_key_id: str = AGENT_SIGNING_KEY_ID
    auto_update: bool = True
    releases: list[AgentReleaseAsset] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_release_set(self) -> "AgentUpdateManifest":
        identities = [(release.platform, release.version) for release in self.releases]
        if len(identities) != len(set(identities)):
            raise ValueError("manifesto possui release duplicada")
        if self.auto_update and not self.releases:
            raise ValueError("manifesto com auto_update exige release")
        if self.auto_update and not any(
            release.version == self.recommended_version for release in self.releases
        ):
            raise ValueError("versão recomendada não possui release")
        return self


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
    del public_base_url
    return AgentUpdateManifest(auto_update=False, releases=[])


def _with_local_release_assets(manifest: AgentUpdateManifest, public_base_url: str | None) -> AgentUpdateManifest:
    release_dir = Path(__file__).resolve().parent / "data" / "agent_releases"
    releases: list[AgentReleaseAsset] = []
    for release in manifest.releases:
        route_platform = release.platform.replace("/", "-")
        filename = f"printora-agent-{route_platform}-{release.version}"
        path = release_dir / filename
        if not path.exists() or not path.is_file():
            raise RuntimeError(f"artefato do agente ausente: {filename}")
        actual_sha256 = _sha256_file(path)
        if actual_sha256 != release.sha256:
            raise RuntimeError(f"checksum divergente para {filename}")
        url = release.url
        if public_base_url:
            url = (
                f"{public_base_url.rstrip('/')}/api/agent/update/releases/"
                f"{release.version}/{route_platform}"
            )
        releases.append(release.model_copy(update={"url": url}))
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
