from __future__ import annotations

from datetime import timedelta
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.auth import AuthUser, format_dt, hash_token, new_secret, utc_now
from app.database import connect_database
from app.printers import PrinterRecord, PrinterRepository


PAIRING_TOKEN_TTL = timedelta(minutes=15)
AgentStatus = Literal["active", "revoked"]


class PairingTokenCreateRequest(BaseModel):
    ttl_minutes: int = Field(default=15, ge=1, le=60)


class PairingTokenResponse(BaseModel):
    id: int
    printer_id: int
    token: str
    token_prefix: str
    expires_at: str
    created_at: str


class PairingTokenRecord(BaseModel):
    id: int
    printer_id: int
    token_prefix: str
    status: Literal["active", "used", "revoked", "expired"]
    expires_at: str
    created_at: str
    consumed_at: str | None = None
    revoked_at: str | None = None


class AgentExchangeRequest(BaseModel):
    pairing_token: str = Field(min_length=20, max_length=240)
    stable_id: str = Field(min_length=3, max_length=160)
    agent_version: str | None = Field(default=None, max_length=80)
    platform: str | None = Field(default=None, max_length=120)
    capabilities: dict[str, Any] = Field(default_factory=dict)

    @field_validator("stable_id")
    @classmethod
    def clean_stable_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("identidade do agente é obrigatória")
        return cleaned


class AgentCredentialExchangeResponse(BaseModel):
    agent_id: int
    printer_id: int
    credential: str
    credential_prefix: str
    status: AgentStatus


class AgentRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    stable_id: str
    credential_prefix: str
    agent_version: str | None
    platform: str | None
    capabilities: dict[str, Any]
    status: AgentStatus
    paired_at: str
    last_seen_at: str | None
    revoked_at: str | None
    rotated_at: str | None


class AgentPairingOverview(BaseModel):
    printer_id: int
    pairing_tokens: list[PairingTokenRecord]
    agents: list[AgentRecord]


class AgentHeartbeatRequest(BaseModel):
    agent_version: str | None = Field(default=None, max_length=80)
    platform: str | None = Field(default=None, max_length=120)
    capabilities: dict[str, Any] = Field(default_factory=dict)


class AgentHeartbeatResponse(BaseModel):
    accepted: bool
    agent_id: int
    printer_id: int
    status: AgentStatus


class AgentSnapshotRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentJobResponse(BaseModel):
    jobs: list[dict[str, Any]] = Field(default_factory=list)


class AgentEventRecord(BaseModel):
    id: int
    printer_id: int
    agent_id: int | None
    event_type: str
    status: str
    detail: str | None
    created_at: str


class AgentPairingRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create_pairing_token(self, current_user: AuthUser, printer: PrinterRecord, request: PairingTokenCreateRequest) -> PairingTokenResponse:
        token = new_secret("ptr_pair")
        expires_at = utc_now() + timedelta(minutes=request.ttl_minutes)
        token_prefix = token[:18]
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO printer_pairing_tokens (
                    printer_id, organization_id, owner_user_id, created_by_user_id,
                    token_hash, token_prefix, expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer.id,
                    printer.organization_id,
                    printer.owner_user_id,
                    current_user.id,
                    hash_token(token),
                    token_prefix,
                    format_dt(expires_at),
                ),
            )
            row = connection.execute(
                "SELECT id, printer_id, token_prefix, expires_at, created_at FROM printer_pairing_tokens WHERE id = ?",
                (int(cursor.lastrowid),),
            ).fetchone()
            self._record_event(connection, printer.id, None, "pairing_token_created", "ok", token_prefix)
        return PairingTokenResponse(
            id=int(row["id"]),
            printer_id=int(row["printer_id"]),
            token=token,
            token_prefix=str(row["token_prefix"]),
            expires_at=str(row["expires_at"]),
            created_at=str(row["created_at"]),
        )

    def overview(self, printer_id: int) -> AgentPairingOverview:
        with connect_database(self.database_path) as connection:
            token_rows = connection.execute(
                """
                SELECT id, printer_id, token_prefix, expires_at, consumed_at, revoked_at, created_at
                FROM printer_pairing_tokens
                WHERE printer_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 20
                """,
                (printer_id,),
            ).fetchall()
            agent_rows = connection.execute(
                """
                SELECT *
                FROM printer_agents
                WHERE printer_id = ?
                ORDER BY paired_at DESC, id DESC
                """,
                (printer_id,),
            ).fetchall()
        return AgentPairingOverview(
            printer_id=printer_id,
            pairing_tokens=[_pairing_token_from_row(row) for row in token_rows],
            agents=[_agent_from_row(row) for row in agent_rows],
        )

    def revoke_pairing_token(self, printer_id: int, token_id: int) -> PairingTokenRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id
                FROM printer_pairing_tokens
                WHERE id = ? AND printer_id = ?
                """,
                (token_id, printer_id),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                """
                UPDATE printer_pairing_tokens
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE id = ? AND consumed_at IS NULL AND revoked_at IS NULL
                """,
                (token_id,),
            )
            self._record_event(connection, printer_id, None, "pairing_token_revoked", "ok", f"token:{token_id}")
            updated = connection.execute(
                """
                SELECT id, printer_id, token_prefix, expires_at, consumed_at, revoked_at, created_at
                FROM printer_pairing_tokens
                WHERE id = ?
                """,
                (token_id,),
            ).fetchone()
        return _pairing_token_from_row(updated)

    def exchange_token(self, request: AgentExchangeRequest) -> AgentCredentialExchangeResponse:
        token_hash = hash_token(request.pairing_token)
        credential = new_secret("ptr_agent")
        credential_prefix = credential[:18]
        now_text = format_dt(utc_now())
        with connect_database(self.database_path) as connection:
            token_row = connection.execute(
                """
                SELECT t.*, p.id AS visible_printer_id
                FROM printer_pairing_tokens t
                JOIN printers p ON p.id = t.printer_id
                WHERE t.token_hash = ?
                """,
                (token_hash,),
            ).fetchone()
            if token_row is None:
                raise ValueError("token de pareamento inválido")
            printer_id = int(token_row["printer_id"])
            if token_row["revoked_at"] is not None:
                self._record_event(connection, printer_id, None, "pairing_failed", "revoked_token", str(token_row["token_prefix"]))
                raise ValueError("token de pareamento revogado")
            if token_row["consumed_at"] is not None:
                self._record_event(connection, printer_id, None, "pairing_failed", "used_token", str(token_row["token_prefix"]))
                raise ValueError("token de pareamento já usado")
            if str(token_row["expires_at"]) <= now_text:
                self._record_event(connection, printer_id, None, "pairing_failed", "expired_token", str(token_row["token_prefix"]))
                raise ValueError("token de pareamento expirado")

            existing = connection.execute(
                "SELECT id FROM printer_agents WHERE stable_id = ?",
                (request.stable_id,),
            ).fetchone()
            if existing is not None:
                raise ValueError("identidade do agente já pareada")
            cursor = connection.execute(
                """
                INSERT INTO printer_agents (
                    printer_id, organization_id, owner_user_id, stable_id, credential_hash,
                    credential_prefix, agent_version, platform, capabilities_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    token_row["organization_id"],
                    token_row["owner_user_id"],
                    request.stable_id,
                    hash_token(credential),
                    credential_prefix,
                    request.agent_version,
                    request.platform,
                    json.dumps(request.capabilities),
                ),
            )
            agent_id = int(cursor.lastrowid)
            connection.execute(
                "UPDATE printer_pairing_tokens SET consumed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (int(token_row["id"]),),
            )
            self._record_event(connection, printer_id, agent_id, "paired", "ok", request.platform)
        return AgentCredentialExchangeResponse(
            agent_id=agent_id,
            printer_id=printer_id,
            credential=credential,
            credential_prefix=credential_prefix,
            status="active",
        )

    def rotate_agent_credential(self, printer_id: int, agent_id: int) -> AgentCredentialExchangeResponse | None:
        credential = new_secret("ptr_agent")
        credential_prefix = credential[:18]
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT id FROM printer_agents WHERE id = ? AND printer_id = ?",
                (agent_id, printer_id),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                """
                UPDATE printer_agents
                SET credential_hash = ?, credential_prefix = ?, rotated_at = CURRENT_TIMESTAMP, status = 'active', revoked_at = NULL
                WHERE id = ?
                """,
                (hash_token(credential), credential_prefix, agent_id),
            )
            self._record_event(connection, printer_id, agent_id, "credential_rotated", "ok", credential_prefix)
        return AgentCredentialExchangeResponse(
            agent_id=agent_id,
            printer_id=printer_id,
            credential=credential,
            credential_prefix=credential_prefix,
            status="active",
        )

    def revoke_agent(self, printer_id: int, agent_id: int) -> AgentRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT id FROM printer_agents WHERE id = ? AND printer_id = ?",
                (agent_id, printer_id),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                """
                UPDATE printer_agents
                SET status = 'revoked', revoked_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (agent_id,),
            )
            self._record_event(connection, printer_id, agent_id, "agent_revoked", "ok", None)
            updated = connection.execute("SELECT * FROM printer_agents WHERE id = ?", (agent_id,)).fetchone()
        return _agent_from_row(updated)

    def authenticate_agent(self, credential: str) -> AgentRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM printer_agents
                WHERE credential_hash = ? AND status = 'active' AND revoked_at IS NULL
                """,
                (hash_token(credential),),
            ).fetchone()
        return _agent_from_row(row) if row else None

    def heartbeat(self, agent: AgentRecord, request: AgentHeartbeatRequest) -> AgentHeartbeatResponse:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE printer_agents
                SET last_seen_at = CURRENT_TIMESTAMP,
                    agent_version = COALESCE(?, agent_version),
                    platform = COALESCE(?, platform),
                    capabilities_json = ?
                WHERE id = ? AND status = 'active' AND revoked_at IS NULL
                """,
                (request.agent_version, request.platform, json.dumps(request.capabilities), agent.id),
            )
            self._record_event(connection, agent.printer_id, agent.id, "heartbeat", "ok", request.agent_version)
        return AgentHeartbeatResponse(accepted=True, agent_id=agent.id, printer_id=agent.printer_id, status="active")

    def store_snapshot(self, agent: AgentRecord, request: AgentSnapshotRequest) -> AgentHeartbeatResponse:
        with connect_database(self.database_path) as connection:
            connection.execute(
                "UPDATE printer_agents SET last_seen_at = CURRENT_TIMESTAMP WHERE id = ?",
                (agent.id,),
            )
            self._record_event(connection, agent.printer_id, agent.id, "snapshot", "ok", _snapshot_summary(request.payload))
        return AgentHeartbeatResponse(accepted=True, agent_id=agent.id, printer_id=agent.printer_id, status="active")

    def list_events(self, printer_id: int, limit: int = 50) -> list[AgentEventRecord]:
        clean_limit = max(1, min(limit, 100))
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, agent_id, event_type, status, detail, created_at
                FROM printer_agent_events
                WHERE printer_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, clean_limit),
            ).fetchall()
        return [_event_from_row(row) for row in rows]

    def _record_event(self, connection, printer_id: int, agent_id: int | None, event_type: str, status: str, detail: str | None) -> None:
        connection.execute(
            """
            INSERT INTO printer_agent_events (printer_id, agent_id, event_type, status, detail)
            VALUES (?, ?, ?, ?, ?)
            """,
            (printer_id, agent_id, event_type, status, _sanitize_detail(detail)),
        )


def printer_for_user(database_path: Path, user: AuthUser, printer_id: int) -> PrinterRecord | None:
    return PrinterRepository(
        database_path,
        user_id=user.id,
        organization_ids=tuple(organization.id for organization in user.organizations),
    ).get_printer(printer_id)


def _pairing_token_from_row(row) -> PairingTokenRecord:
    status: Literal["active", "used", "revoked", "expired"] = "active"
    if row["revoked_at"] is not None:
        status = "revoked"
    elif row["consumed_at"] is not None:
        status = "used"
    elif str(row["expires_at"]) <= format_dt(utc_now()):
        status = "expired"
    return PairingTokenRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        token_prefix=str(row["token_prefix"]),
        status=status,
        expires_at=str(row["expires_at"]),
        created_at=str(row["created_at"]),
        consumed_at=row["consumed_at"],
        revoked_at=row["revoked_at"],
    )


def _agent_from_row(row) -> AgentRecord:
    return AgentRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        stable_id=str(row["stable_id"]),
        credential_prefix=str(row["credential_prefix"]),
        agent_version=row["agent_version"],
        platform=row["platform"],
        capabilities=json.loads(row["capabilities_json"] or "{}"),
        status=row["status"],
        paired_at=str(row["paired_at"]),
        last_seen_at=row["last_seen_at"],
        revoked_at=row["revoked_at"],
        rotated_at=row["rotated_at"],
    )


def _event_from_row(row) -> AgentEventRecord:
    return AgentEventRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        agent_id=int(row["agent_id"]) if row["agent_id"] is not None else None,
        event_type=str(row["event_type"]),
        status=str(row["status"]),
        detail=row["detail"],
        created_at=str(row["created_at"]),
    )


def _snapshot_summary(payload: dict[str, Any]) -> str:
    keys = sorted(str(key) for key in payload.keys())[:8]
    return "keys:" + ",".join(keys)


def _sanitize_detail(detail: str | None) -> str | None:
    if detail is None:
        return None
    return detail[:160]
