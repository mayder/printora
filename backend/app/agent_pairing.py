from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
from uuid import uuid4
from typing import Any, Literal

from app.auth import AuthUser, format_dt, hash_token, new_secret, utc_now
from app.database import connect_database
from app.modules.platform.database_target import uses_postgresql
from app.modules.platform.durable_execution import (
    DurableExecutionRepository,
    EventEnvelope,
)
from app.modules.operations.contracts import (
    AGENT_PROTOCOL_VERSION,
    AGENT_MAX_PAYLOAD_BYTES,
    AGENT_MAX_RESULT_BYTES,
    EXPECTED_AGENT_VERSION,
    AgentStatus,
    AgentJobStatus,
    AgentMessageType,
    AgentPairingConflictError,
    PairingTokenCreateRequest,
    PairingTokenResponse,
    AgentInstallPlanResponse,
    PairingTokenRecord,
    AgentExchangeRequest,
    AgentCredentialExchangeResponse,
    AgentRecord,
    AgentPairingOverview,
    AgentInstallStatusResponse,
    AgentHeartbeatRequest,
    AgentHeartbeatResponse,
    AgentSnapshotRequest,
    AgentProtocolMessage,
    AgentJobCreateRequest,
    AgentJobRecord,
    AgentJobResponse,
    AgentJobResultRequest,
    AgentJobErrorRequest,
    AgentEventRecord,
)
from app.printers import AGENT_ONLINE_WINDOW_SECONDS, PrinterRecord, PrinterRepository


PAIRING_TOKEN_TTL = timedelta(minutes=15)
AGENT_JOB_TTL = timedelta(minutes=2)
AGENT_JOB_IN_PROGRESS_TIMEOUT = timedelta(minutes=5)


def _active_job_expiration_condition() -> str:
    if uses_postgresql():
        return (
            "(expires_at IS NULL OR "
            "(expires_at::timestamp AT TIME ZONE 'UTC') > NOW())"
        )
    return "(expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)"


def _pending_job_expiration_condition() -> str:
    if uses_postgresql():
        return "(expires_at::timestamp AT TIME ZONE 'UTC') <= NOW()"
    return "expires_at <= CURRENT_TIMESTAMP"


def _in_progress_job_expiration_condition() -> tuple[str, tuple[object, ...]]:
    if uses_postgresql():
        return (
            "updated_at::timestamptz <= NOW() - INTERVAL '5 minutes'",
            (),
        )
    return (
        "updated_at <= datetime(CURRENT_TIMESTAMP, ?)",
        (f"-{int(AGENT_JOB_IN_PROGRESS_TIMEOUT.total_seconds())} seconds",),
    )


def _acquire_agent_job_coalescence_lock(connection, printer_id: int, request: AgentJobCreateRequest) -> None:
    if not uses_postgresql():
        return
    payload = json.dumps(request.payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    lock_scope = f"{printer_id}\0{request.agent_id or 0}\0{request.job_type}\0{payload}".encode()
    lock_key = int.from_bytes(hashlib.sha256(lock_scope).digest()[:8], "big", signed=True)
    connection.execute(
        "SELECT pg_advisory_xact_lock(?) AS acquired",
        (lock_key,),
    ).fetchone()










































class AgentPairingRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def create_pairing_token(self, current_user: AuthUser, printer: PrinterRecord, request: PairingTokenCreateRequest) -> PairingTokenResponse:
        token = new_secret("ptr_pair")
        expires_at = utc_now() + timedelta(minutes=request.ttl_minutes)
        token_prefix = token[:18]
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE printer_pairing_tokens
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE printer_id = ?
                  AND consumed_at IS NULL
                  AND revoked_at IS NULL
                  AND expires_at > CURRENT_TIMESTAMP
                """,
                (printer.id,),
            )
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

    def create_install_plan(
        self,
        current_user: AuthUser,
        printer: PrinterRecord,
        api_base_url: str,
        agent_bin_url: str | None = None,
        agent_sha256: str | None = None,
        agent_signature: str | None = None,
    ) -> AgentInstallPlanResponse:
        token = self.create_pairing_token(current_user, printer, PairingTokenCreateRequest(ttl_minutes=15))
        script_url = f"{api_base_url.rstrip('/')}/api/agent/install/linux.sh"
        bin_env = f"PRINTORA_AGENT_BIN_URL={_shell_quote(agent_bin_url)} " if agent_bin_url else ""
        hash_env = f"PRINTORA_AGENT_SHA256={_shell_quote(agent_sha256)} " if agent_sha256 else ""
        signature_env = (
            f"PRINTORA_AGENT_SIGNATURE={_shell_quote(agent_signature)} "
            if agent_signature
            else ""
        )
        install_command = (
            f"curl -fsSL {_shell_quote(script_url)} | "
            f"sudo PRINTORA_API_BASE={_shell_quote(api_base_url.rstrip('/'))} "
            f"PRINTORA_PAIRING_TOKEN={_shell_quote(token.token)} "
            f"PRINTORA_AGENT_VERSION={_shell_quote(EXPECTED_AGENT_VERSION)} "
            f"{bin_env}{hash_env}{signature_env}"
            "PRINTORA_MOONRAKER_URL='http://127.0.0.1:7125' "
            "bash -s -- --apply --yes"
        )
        preflight_command = (
            f"curl -fsSL {_shell_quote(script_url)} | "
            f"PRINTORA_API_BASE={_shell_quote(api_base_url.rstrip('/'))} "
            "PRINTORA_MOONRAKER_URL='http://127.0.0.1:7125' "
            "bash -s -- --preflight"
        )
        uninstall_command = f"curl -fsSL {_shell_quote(script_url)} | sudo bash -s -- --uninstall"
        return AgentInstallPlanResponse(
            printer_id=printer.id,
            token_id=token.id,
            token_prefix=token.token_prefix,
            expires_at=token.expires_at,
            expected_agent_version=EXPECTED_AGENT_VERSION,
            script_url=script_url,
            preflight_command=preflight_command,
            install_command=install_command,
            uninstall_command=uninstall_command,
        )

    def overview(self, printer_id: int) -> AgentPairingOverview:
        with connect_database(self.database_path) as connection:
            token_rows = connection.execute(
                """
                SELECT id, printer_id, token_prefix, expires_at, consumed_at, revoked_at, removed_at, created_at
                FROM printer_pairing_tokens
                WHERE printer_id = ? AND removed_at IS NULL
                ORDER BY created_at DESC, id DESC
                LIMIT 20
                """,
                (printer_id,),
            ).fetchall()
            agent_rows = connection.execute(
                """
                SELECT *
                FROM printer_agents
                WHERE printer_id = ? AND status != 'removed' AND removed_at IS NULL
                ORDER BY paired_at DESC, id DESC
                """,
                (printer_id,),
            ).fetchall()
        return AgentPairingOverview(
            printer_id=printer_id,
            pairing_tokens=[_pairing_token_from_row(row) for row in token_rows],
            agents=[_agent_from_row(row) for row in agent_rows],
        )

    def install_status(self, printer_id: int) -> AgentInstallStatusResponse:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM printer_agents
                WHERE printer_id = ? AND status = 'active' AND revoked_at IS NULL
                ORDER BY last_seen_at IS NULL, last_seen_at DESC, paired_at DESC, id DESC
                """,
                (printer_id,),
            ).fetchall()
        latest = _agent_from_row(rows[0]) if rows else None
        latest_online = bool(latest and _last_seen_age_seconds(latest.last_seen_at) is not None and _last_seen_age_seconds(latest.last_seen_at) <= AGENT_ONLINE_WINDOW_SECONDS)
        ready = bool(latest_online and latest and latest.agent_version == EXPECTED_AGENT_VERSION)
        diagnostic = "agente online"
        if latest is None:
            diagnostic = "nenhum agente ativo pareado"
        elif latest.last_seen_at is None:
            diagnostic = "agente pareado, aguardando heartbeat"
        elif not latest_online:
            diagnostic = "agente pareado, mas offline; revogue/remova o agente antigo antes de reinstalar no mesmo host"
        elif latest.agent_version != EXPECTED_AGENT_VERSION:
            diagnostic = f"agente online em versão antiga: {latest.agent_version or '-'}, esperado {EXPECTED_AGENT_VERSION}"
        return AgentInstallStatusResponse(
            printer_id=printer_id,
            expected_agent_version=EXPECTED_AGENT_VERSION,
            ready=ready,
            active_agents=len(rows),
            latest_agent_id=latest.id if latest else None,
            latest_stable_id=latest.stable_id if latest else None,
            latest_version=latest.agent_version if latest else None,
            latest_platform=latest.platform if latest else None,
            latest_last_seen_at=latest.last_seen_at if latest else None,
            diagnostic=diagnostic,
        )

    def revoke_pairing_token(self, printer_id: int, token_id: int) -> PairingTokenRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, consumed_at, revoked_at, removed_at, expires_at
                FROM printer_pairing_tokens
                WHERE id = ? AND printer_id = ? AND removed_at IS NULL
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
                SELECT id, printer_id, token_prefix, expires_at, consumed_at, revoked_at, removed_at, created_at
                FROM printer_pairing_tokens
                WHERE id = ?
                """,
                (token_id,),
            ).fetchone()
        return _pairing_token_from_row(updated)

    def remove_pairing_token(self, printer_id: int, token_id: int) -> PairingTokenRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, consumed_at, revoked_at, removed_at, expires_at
                FROM printer_pairing_tokens
                WHERE id = ? AND printer_id = ? AND removed_at IS NULL
                """,
                (token_id, printer_id),
            ).fetchone()
            if row is None:
                return None
            if _pairing_token_status(row) == "active":
                raise ValueError("revogue o token antes de remover")
            connection.execute(
                """
                UPDATE printer_pairing_tokens
                SET removed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (token_id,),
            )
            self._record_event(connection, printer_id, None, "pairing_token_removed", "ok", f"token:{token_id}")
            updated = connection.execute(
                """
                SELECT id, printer_id, token_prefix, expires_at, consumed_at, revoked_at, removed_at, created_at
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
                "SELECT id, status FROM printer_agents WHERE stable_id = ?",
                (request.stable_id,),
            ).fetchone()
            if existing is not None and existing["status"] != "removed":
                raise AgentPairingConflictError(request.stable_id)
            if existing is not None:
                agent_id = int(existing["id"])
                connection.execute(
                    """
                    UPDATE printer_agents
                    SET printer_id = ?, organization_id = ?, owner_user_id = ?, credential_hash = ?,
                        credential_prefix = ?, agent_version = ?, platform = ?, capabilities_json = ?,
                        status = 'active', paired_at = CURRENT_TIMESTAMP, last_seen_at = NULL,
                        revoked_at = NULL, removed_at = NULL, rotated_at = NULL
                    WHERE id = ?
                    """,
                    (
                        printer_id,
                        token_row["organization_id"],
                        token_row["owner_user_id"],
                        hash_token(credential),
                        credential_prefix,
                        request.agent_version,
                        request.platform,
                        json.dumps(request.capabilities),
                        agent_id,
                    ),
                )
            else:
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
                "SELECT id FROM printer_agents WHERE id = ? AND printer_id = ? AND status != 'removed'",
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

    def remove_agent(self, printer_id: int, agent_id: int) -> AgentRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT id FROM printer_agents WHERE id = ? AND printer_id = ? AND status != 'removed'",
                (agent_id, printer_id),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                """
                UPDATE printer_agents
                SET status = 'removed',
                    revoked_at = COALESCE(revoked_at, CURRENT_TIMESTAMP),
                    removed_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (agent_id,),
            )
            self._record_event(connection, printer_id, agent_id, "agent_removed", "ok", None)
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
            self._reconcile_agent_update_jobs(connection, agent, request)
            self._record_event(connection, agent.printer_id, agent.id, "heartbeat", "ok", request.agent_version)
        return AgentHeartbeatResponse(accepted=True, agent_id=agent.id, printer_id=agent.printer_id, status="active")

    def store_snapshot(self, agent: AgentRecord, request: AgentSnapshotRequest) -> AgentHeartbeatResponse:
        _ensure_payload_size(request.payload)
        with connect_database(self.database_path) as connection:
            connection.execute(
                "UPDATE printer_agents SET last_seen_at = CURRENT_TIMESTAMP WHERE id = ?",
                (agent.id,),
            )
            self._record_event(connection, agent.printer_id, agent.id, "snapshot", "ok", _snapshot_summary(request.payload))
        return AgentHeartbeatResponse(accepted=True, agent_id=agent.id, printer_id=agent.printer_id, status="active")

    def create_job(self, printer: PrinterRecord, request: AgentJobCreateRequest) -> AgentJobRecord:
        return self._create_job(printer, request, reuse_active=False)

    def create_or_reuse_job(self, printer: PrinterRecord, request: AgentJobCreateRequest) -> AgentJobRecord:
        return self._create_job(printer, request, reuse_active=True)

    def _create_job(
        self,
        printer: PrinterRecord,
        request: AgentJobCreateRequest,
        *,
        reuse_active: bool,
    ) -> AgentJobRecord:
        _ensure_payload_size(request.payload)
        correlation_id = request.correlation_id or f"job_{uuid4().hex}"
        expires_at = request.expires_at or format_dt(utc_now() + AGENT_JOB_TTL)
        with connect_database(self.database_path) as connection:
            if reuse_active:
                _acquire_agent_job_coalescence_lock(connection, printer.id, request)
            self._expire_jobs(connection, printer.id)
            if request.agent_id is not None:
                agent_row = connection.execute(
                    "SELECT id FROM printer_agents WHERE id = ? AND printer_id = ? AND status = 'active' AND revoked_at IS NULL",
                    (request.agent_id, printer.id),
                ).fetchone()
                if agent_row is None:
                    raise ValueError("agente não pertence à impressora")
            if reuse_active:
                active_rows = connection.execute(
                    f"""
                    SELECT *
                    FROM agent_jobs
                    WHERE printer_id = ?
                      AND agent_id = ?
                      AND job_type = ?
                      AND status IN ('pending', 'in_progress')
                      AND {_active_job_expiration_condition()}
                    ORDER BY id DESC
                    LIMIT 20
                    """,
                    (printer.id, request.agent_id, request.job_type),
                ).fetchall()
                for active_row in active_rows:
                    try:
                        active_payload = json.loads(active_row["payload_json"] or "{}")
                    except (TypeError, ValueError):
                        continue
                    if active_payload == request.payload:
                        return _job_from_row(active_row)
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO agent_jobs (printer_id, agent_id, correlation_id, job_type, payload_json, expires_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (printer.id, request.agent_id, correlation_id, request.job_type, json.dumps(request.payload), expires_at),
                )
            except Exception as exc:
                raise ValueError("correlation_id já usado") from exc
            job_id = int(cursor.lastrowid)
            DurableExecutionRepository(self.database_path).append_event(
                connection,
                EventEnvelope(
                    event_id=f"agent-job:{job_id}:created",
                    aggregate_type="agent_job",
                    aggregate_id=str(job_id),
                    event_type="agent.job.created",
                    ordering_key=f"printer:{printer.id}:agent-jobs",
                    sequence_no=job_id,
                    payload={
                        "job_id": job_id,
                        "printer_id": printer.id,
                        "agent_id": request.agent_id,
                        "correlation_id": correlation_id,
                    },
                    headers={"owner_type": "printer", "owner_id": str(printer.id)},
                ),
            )
            self._record_event(connection, printer.id, request.agent_id, "job_created", "pending", request.job_type)
            row = connection.execute("SELECT * FROM agent_jobs WHERE id = ?", (job_id,)).fetchone()
        return _job_from_row(row)

    def get_job(self, printer_id: int, job_id: int) -> AgentJobRecord | None:
        with connect_database(self.database_path) as connection:
            self._expire_jobs(connection, printer_id)
            row = connection.execute(
                "SELECT * FROM agent_jobs WHERE id = ? AND printer_id = ?",
                (job_id, printer_id),
            ).fetchone()
        return _job_from_row(row) if row else None

    def latest_active_agent(self, printer_id: int, *, max_age_seconds: int = 120) -> AgentRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM printer_agents
                WHERE printer_id = ?
                  AND status = 'active'
                  AND revoked_at IS NULL
                  AND last_seen_at IS NOT NULL
                  AND last_seen_at >= datetime('now', ?)
                ORDER BY last_seen_at DESC, paired_at DESC, id DESC
                LIMIT 1
                """,
                (printer_id, f"-{max(1, int(max_age_seconds))} seconds"),
            ).fetchone()
        return _agent_from_row(row) if row else None

    def next_jobs(self, agent: AgentRecord, limit: int = 5) -> AgentJobResponse:
        clean_limit = max(1, min(limit, 20))
        with connect_database(self.database_path) as connection:
            self._expire_jobs(connection, agent.printer_id)
            rows = connection.execute(
                f"""
                SELECT *
                FROM agent_jobs
                WHERE printer_id = ?
                  AND (status = 'pending' OR (status = 'in_progress' AND agent_id = ?))
                  AND (agent_id IS NULL OR agent_id = ?)
                  AND available_at <= CURRENT_TIMESTAMP
                  AND {_active_job_expiration_condition()}
                ORDER BY created_at, id
                LIMIT ?
                """,
                (agent.printer_id, agent.id, agent.id, clean_limit),
            ).fetchall()
        return AgentJobResponse(jobs=[_job_from_row(row) for row in rows])

    def ack_job(self, agent: AgentRecord, job_id: int) -> AgentJobRecord | None:
        with connect_database(self.database_path) as connection:
            row = self._job_for_agent(connection, agent, job_id)
            if row is None:
                return None
            if row["status"] == "pending":
                connection.execute(
                    """
                    UPDATE agent_jobs
                    SET status = 'in_progress', agent_id = ?, attempts = attempts + 1,
                        acked_at = COALESCE(acked_at, CURRENT_TIMESTAMP), updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND status = 'pending'
                    """,
                    (agent.id, job_id),
                )
                self._record_event(connection, agent.printer_id, agent.id, "job_ack", "in_progress", str(row["correlation_id"]))
            updated = connection.execute("SELECT * FROM agent_jobs WHERE id = ?", (job_id,)).fetchone()
        return _job_from_row(updated)

    def nack_job(self, agent: AgentRecord, job_id: int, reason: str = "nack") -> AgentJobRecord | None:
        with connect_database(self.database_path) as connection:
            row = self._job_for_agent(connection, agent, job_id)
            if row is None:
                return None
            if row["status"] in {"pending", "in_progress"}:
                connection.execute(
                    """
                    UPDATE agent_jobs
                    SET status = 'pending', agent_id = NULL, error_message = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (_sanitize_detail(reason), job_id),
                )
                self._record_event(connection, agent.printer_id, agent.id, "job_nack", "pending", str(row["correlation_id"]))
            updated = connection.execute("SELECT * FROM agent_jobs WHERE id = ?", (job_id,)).fetchone()
        return _job_from_row(updated)

    def finish_job(self, agent: AgentRecord, job_id: int, request: AgentJobResultRequest) -> AgentJobRecord | None:
        _ensure_result_size(request.result)
        with connect_database(self.database_path) as connection:
            row = self._job_for_agent(connection, agent, job_id, request.correlation_id)
            if row is None:
                return None
            if row["status"] not in {"succeeded", "failed", "canceled"}:
                connection.execute(
                    """
                    UPDATE agent_jobs
                    SET status = 'succeeded', agent_id = ?, result_json = ?, error_message = NULL,
                        finished_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (agent.id, json.dumps(request.result), job_id),
                )
                self._record_event(connection, agent.printer_id, agent.id, "job_result", "succeeded", request.correlation_id)
            updated = connection.execute("SELECT * FROM agent_jobs WHERE id = ?", (job_id,)).fetchone()
        return _job_from_row(updated)

    def fail_job(self, agent: AgentRecord, job_id: int, request: AgentJobErrorRequest) -> AgentJobRecord | None:
        _ensure_result_size(request.result)
        with connect_database(self.database_path) as connection:
            row = self._job_for_agent(connection, agent, job_id, request.correlation_id)
            if row is None:
                return None
            if row["status"] not in {"succeeded", "failed", "canceled"}:
                connection.execute(
                    """
                    UPDATE agent_jobs
                    SET status = 'failed', agent_id = ?, result_json = ?, error_message = ?,
                        finished_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (agent.id, json.dumps(request.result), _sanitize_detail(request.error_message), job_id),
                )
                self._record_event(connection, agent.printer_id, agent.id, "job_error", "failed", request.correlation_id)
            updated = connection.execute("SELECT * FROM agent_jobs WHERE id = ?", (job_id,)).fetchone()
        return _job_from_row(updated)

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

    def _job_for_agent(self, connection, agent: AgentRecord, job_id: int, correlation_id: str | None = None):
        parameters: tuple[Any, ...]
        sql = """
            SELECT *
            FROM agent_jobs
            WHERE id = ?
              AND printer_id = ?
              AND (agent_id IS NULL OR agent_id = ?)
        """
        parameters = (job_id, agent.printer_id, agent.id)
        if correlation_id is not None:
            sql += " AND correlation_id = ?"
            parameters = (job_id, agent.printer_id, agent.id, correlation_id)
        return connection.execute(sql, parameters).fetchone()

    def _expire_jobs(self, connection, printer_id: int) -> None:
        connection.execute(
            f"""
            UPDATE agent_jobs
            SET status = 'failed',
                error_message = 'job expirado antes do agente consumir',
                finished_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE printer_id = ?
              AND status = 'pending'
              AND expires_at IS NOT NULL
              AND {_pending_job_expiration_condition()}
            """,
            (printer_id,),
        )
        in_progress_condition, in_progress_parameters = (
            _in_progress_job_expiration_condition()
        )
        connection.execute(
            f"""
            UPDATE agent_jobs
            SET status = 'failed',
                error_message = 'job em execução expirou sem retorno do agente',
                finished_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE printer_id = ?
              AND status = 'in_progress'
              AND {in_progress_condition}
            """,
            (printer_id, *in_progress_parameters),
        )

    def _reconcile_agent_update_jobs(self, connection, agent: AgentRecord, request: AgentHeartbeatRequest) -> None:
        if not request.agent_version:
            return
        rows = connection.execute(
            """
            SELECT id, correlation_id, payload_json
            FROM agent_jobs
            WHERE printer_id = ?
              AND agent_id = ?
              AND job_type = 'remote_agent_update_check'
              AND status IN ('pending', 'in_progress')
            ORDER BY created_at DESC, id DESC
            LIMIT 10
            """,
            (agent.printer_id, agent.id),
        ).fetchall()
        for row in rows:
            payload = json.loads(row["payload_json"] or "{}")
            target_version = str(payload.get("target_version") or EXPECTED_AGENT_VERSION)
            if request.agent_version != target_version:
                continue
            result = {
                "safe_mode": "agent_self_update",
                "status": "applied",
                "current_version": request.agent_version,
                "target_version": target_version,
                "detail": "update confirmado pelo heartbeat após reinício do agente",
            }
            connection.execute(
                """
                UPDATE agent_jobs
                SET status = 'succeeded',
                    result_json = ?,
                    error_message = NULL,
                    finished_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                  AND status IN ('pending', 'in_progress')
                """,
                (json.dumps(result), int(row["id"])),
            )
            self._record_event(connection, agent.printer_id, agent.id, "job_result", "succeeded", str(row["correlation_id"]))

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


def _pairing_token_status(row) -> Literal["active", "used", "revoked", "expired", "removed"]:
    if row["removed_at"] is not None:
        return "removed"
    if row["revoked_at"] is not None:
        return "revoked"
    if row["consumed_at"] is not None:
        return "used"
    if str(row["expires_at"]) <= format_dt(utc_now()):
        return "expired"
    return "active"


def _pairing_token_from_row(row) -> PairingTokenRecord:
    status = _pairing_token_status(row)
    return PairingTokenRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        token_prefix=str(row["token_prefix"]),
        status=status,
        expires_at=str(row["expires_at"]),
        created_at=str(row["created_at"]),
        consumed_at=row["consumed_at"],
        revoked_at=row["revoked_at"],
        removed_at=row["removed_at"],
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
        removed_at=row["removed_at"],
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


def _job_from_row(row) -> AgentJobRecord:
    return AgentJobRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        agent_id=int(row["agent_id"]) if row["agent_id"] is not None else None,
        correlation_id=str(row["correlation_id"]),
        job_type=str(row["job_type"]),
        payload=json.loads(row["payload_json"] or "{}"),
        status=row["status"],
        attempts=int(row["attempts"]),
        result=json.loads(row["result_json"]) if row["result_json"] else None,
        error_message=row["error_message"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        acked_at=row["acked_at"],
        finished_at=row["finished_at"],
    )


def _ensure_payload_size(payload: dict[str, Any]) -> None:
    if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > AGENT_MAX_PAYLOAD_BYTES:
        raise ValueError("payload excede o limite do protocolo do agente")


def _ensure_result_size(payload: dict[str, Any]) -> None:
    if len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) > AGENT_MAX_RESULT_BYTES:
        raise ValueError("resultado excede o limite do protocolo do agente")


def _last_seen_age_seconds(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0, int((utc_now() - parsed.astimezone(timezone.utc)).total_seconds()))


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def _snapshot_summary(payload: dict[str, Any]) -> str:
    keys = sorted(str(key) for key in payload.keys())[:8]
    return "keys:" + ",".join(keys)


def _sanitize_detail(detail: str | None) -> str | None:
    if detail is None:
        return None
    return detail[:160]
