from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Protocol
from uuid import uuid4

from app.database import connect_database
from app.modules.platform.database_target import uses_postgresql


TERMINAL_JOB_STATES = {"succeeded", "failed", "dead_letter", "canceled"}
ACTIVE_JOB_STATES = {"queued", "leased"}
QUEUE_ACTIVE_LIMITS = {"critical": 10_000, "default": 5_000, "bulk": 1_000}
OWNER_ACTIVE_LIMIT = 250
MAX_JOB_PAYLOAD_BYTES = 256 * 1024
MAX_EVENT_PAYLOAD_BYTES = 256 * 1024


class QueueSaturatedError(RuntimeError):
    pass


class DatabaseConnection(Protocol):
    def execute(self, statement: str, parameters: tuple[object, ...] = ...): ...


@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    ordering_key: str
    sequence_no: int
    payload: dict[str, Any]
    schema_version: int = 1
    headers: dict[str, Any] | None = None


@dataclass(frozen=True)
class DurableJob:
    id: int
    job_key: str
    queue_name: str
    job_type: str
    schema_version: int
    ordering_key: str | None
    owner_type: str | None
    owner_id: str | None
    payload: dict[str, Any]
    priority: int
    status: str
    attempts: int
    max_attempts: int
    available_at: str
    lease_owner: str | None
    lease_token: str | None
    lease_expires_at: str | None
    result: dict[str, Any] | None
    error_message: str | None


@dataclass(frozen=True)
class OutboxEvent:
    id: int
    event_id: str
    aggregate_type: str
    aggregate_id: str
    event_type: str
    schema_version: int
    ordering_key: str
    sequence_no: int
    payload: dict[str, Any]
    headers: dict[str, Any]
    status: str
    attempts: int
    max_attempts: int
    lease_owner: str | None
    lease_token: str | None
    lease_expires_at: str | None


@dataclass(frozen=True)
class InboxDecision:
    accepted: bool
    duplicate: bool
    status: str


class DurableExecutionRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def append_event(self, connection: DatabaseConnection, event: EventEnvelope) -> int:
        if event.schema_version < 1 or event.sequence_no < 1:
            raise ValueError("schema_version e sequence_no devem ser positivos")
        payload_json = _canonical_json(event.payload)
        if len(payload_json.encode("utf-8")) > MAX_EVENT_PAYLOAD_BYTES:
            raise ValueError("payload do evento excede 256 KB")
        cursor = connection.execute(
            """
            INSERT INTO outbox_events (
                event_id, aggregate_type, aggregate_id, event_type, schema_version,
                ordering_key, sequence_no, payload_json, headers_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.event_id,
                event.aggregate_type,
                event.aggregate_id,
                event.event_type,
                event.schema_version,
                event.ordering_key,
                event.sequence_no,
                payload_json,
                _canonical_json(event.headers or {}),
            ),
        )
        return int(cursor.lastrowid)

    def enqueue_job(
        self,
        *,
        job_key: str,
        queue_name: str,
        job_type: str,
        payload: dict[str, Any],
        schema_version: int = 1,
        ordering_key: str | None = None,
        owner_type: str | None = None,
        owner_id: str | None = None,
        priority: int = 100,
        max_attempts: int = 8,
        available_at: datetime | None = None,
        connection: DatabaseConnection | None = None,
    ) -> DurableJob:
        if not job_key.strip() or not queue_name.strip() or not job_type.strip():
            raise ValueError("job_key, queue_name e job_type são obrigatórios")
        if schema_version < 1 or max_attempts < 1:
            raise ValueError("schema_version e max_attempts devem ser positivos")
        if connection is not None:
            return self._enqueue_job(
                connection,
                job_key=job_key,
                queue_name=queue_name,
                job_type=job_type,
                payload=payload,
                schema_version=schema_version,
                ordering_key=ordering_key,
                owner_type=owner_type,
                owner_id=owner_id,
                priority=priority,
                max_attempts=max_attempts,
                available_at=available_at,
            )
        with connect_database(self.database_path) as managed:
            return self._enqueue_job(
                managed,
                job_key=job_key,
                queue_name=queue_name,
                job_type=job_type,
                payload=payload,
                schema_version=schema_version,
                ordering_key=ordering_key,
                owner_type=owner_type,
                owner_id=owner_id,
                priority=priority,
                max_attempts=max_attempts,
                available_at=available_at,
            )

    def claim_event(self, dispatcher_id: str, lease_seconds: int = 45) -> OutboxEvent | None:
        now = _utc_now()
        token = uuid4().hex
        parameters = (
            dispatcher_id,
            token,
            _timestamp(now + timedelta(seconds=max(5, lease_seconds))),
            _timestamp(now),
            _timestamp(now),
            _timestamp(now),
        )
        with connect_database(self.database_path) as connection:
            self._dead_letter_exhausted_events(connection, now)
            if uses_postgresql():
                row = connection.execute(
                    """
                    WITH candidate AS (
                        SELECT candidate.id
                        FROM outbox_events AS candidate
                        WHERE candidate.status IN ('pending', 'publishing')
                          AND candidate.available_at <= ?
                          AND (candidate.status = 'pending' OR candidate.lease_expires_at <= ?)
                          AND candidate.attempts < candidate.max_attempts
                          AND NOT EXISTS (
                              SELECT 1 FROM outbox_events AS previous
                              WHERE previous.ordering_key = candidate.ordering_key
                                AND previous.sequence_no < candidate.sequence_no
                                AND previous.status <> 'published'
                          )
                        ORDER BY candidate.id
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    )
                    UPDATE outbox_events AS events
                    SET status = 'publishing', attempts = attempts + 1,
                        lease_owner = ?, lease_token = ?, lease_expires_at = ?, updated_at = ?
                    FROM candidate
                    WHERE events.id = candidate.id
                    RETURNING events.*
                    """,
                    (
                        _timestamp(now),
                        _timestamp(now),
                        dispatcher_id,
                        token,
                        _timestamp(now + timedelta(seconds=max(5, lease_seconds))),
                        _timestamp(now),
                    ),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    UPDATE outbox_events
                    SET status = 'publishing', attempts = attempts + 1,
                        lease_owner = ?, lease_token = ?, lease_expires_at = ?, updated_at = ?
                    WHERE id = (
                        SELECT candidate.id
                        FROM outbox_events AS candidate
                        WHERE candidate.status IN ('pending', 'publishing')
                          AND candidate.available_at <= ?
                          AND (candidate.status = 'pending' OR candidate.lease_expires_at <= ?)
                          AND candidate.attempts < candidate.max_attempts
                          AND NOT EXISTS (
                              SELECT 1 FROM outbox_events AS previous
                              WHERE previous.ordering_key = candidate.ordering_key
                                AND previous.sequence_no < candidate.sequence_no
                                AND previous.status <> 'published'
                          )
                        ORDER BY candidate.id
                        LIMIT 1
                    )
                    RETURNING *
                    """,
                    parameters,
                ).fetchone()
        return _outbox_from_row(row) if row else None

    def publish_event(
        self,
        event_id: int,
        lease_token: str,
        *,
        connection: DatabaseConnection | None = None,
    ) -> bool:
        if connection is not None:
            return self._publish_event(connection, event_id, lease_token)
        with connect_database(self.database_path) as managed:
            return self._publish_event(managed, event_id, lease_token)

    def retry_event(self, event_id: int, lease_token: str, error: str, backoff_seconds: int) -> bool:
        now = _utc_now()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT attempts, max_attempts FROM outbox_events WHERE id = ? AND status = 'publishing' AND lease_token = ?",
                (event_id, lease_token),
            ).fetchone()
            if row is None:
                return False
            terminal = int(row["attempts"]) >= int(row["max_attempts"])
            status = "dead_letter" if terminal else "pending"
            updated = connection.execute(
                """
                UPDATE outbox_events
                SET status = ?, last_error = ?, available_at = ?, lease_owner = NULL,
                    lease_token = NULL, lease_expires_at = NULL, updated_at = ?
                WHERE id = ? AND status = 'publishing' AND lease_token = ?
                """,
                (
                    status,
                    _safe_error(error),
                    _timestamp(now + timedelta(seconds=max(1, backoff_seconds))),
                    _timestamp(now),
                    event_id,
                    lease_token,
                ),
            )
        return updated.rowcount == 1

    def claim_job(self, queue_name: str, worker_id: str, lease_seconds: int = 45) -> DurableJob | None:
        now = _utc_now()
        lease_token = uuid4().hex
        lease_expires_at = now + timedelta(seconds=max(5, lease_seconds))
        with connect_database(self.database_path) as connection:
            self._dead_letter_exhausted(connection, queue_name, now)
            if uses_postgresql():
                row = connection.execute(
                    """
                    WITH candidate AS (
                        SELECT id
                        FROM durable_jobs
                        WHERE queue_name = ?
                          AND status IN ('queued', 'leased')
                          AND available_at <= ?
                          AND (status = 'queued' OR lease_expires_at <= ?)
                          AND attempts < max_attempts
                        ORDER BY priority ASC, available_at ASC, id ASC
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    )
                    UPDATE durable_jobs AS jobs
                    SET status = 'leased', attempts = attempts + 1,
                        lease_owner = ?, lease_token = ?, lease_expires_at = ?,
                        heartbeat_at = ?, updated_at = ?
                    FROM candidate
                    WHERE jobs.id = candidate.id
                    RETURNING jobs.*
                    """,
                    (
                        queue_name,
                        _timestamp(now),
                        _timestamp(now),
                        worker_id,
                        lease_token,
                        _timestamp(lease_expires_at),
                        _timestamp(now),
                        _timestamp(now),
                    ),
                ).fetchone()
            else:
                row = connection.execute(
                    """
                    UPDATE durable_jobs
                    SET status = 'leased', attempts = attempts + 1,
                        lease_owner = ?, lease_token = ?, lease_expires_at = ?,
                        heartbeat_at = ?, updated_at = ?
                    WHERE id = (
                        SELECT id
                        FROM durable_jobs
                        WHERE queue_name = ?
                          AND status IN ('queued', 'leased')
                          AND available_at <= ?
                          AND (status = 'queued' OR lease_expires_at <= ?)
                          AND attempts < max_attempts
                        ORDER BY priority ASC, available_at ASC, id ASC
                        LIMIT 1
                    )
                    RETURNING *
                    """,
                    (
                        worker_id,
                        lease_token,
                        _timestamp(lease_expires_at),
                        _timestamp(now),
                        _timestamp(now),
                        queue_name,
                        _timestamp(now),
                        _timestamp(now),
                    ),
                ).fetchone()
        return _job_from_row(row) if row else None

    def heartbeat_job(self, job_id: int, lease_token: str, lease_seconds: int = 45) -> bool:
        now = _utc_now()
        with connect_database(self.database_path) as connection:
            updated = connection.execute(
                """
                UPDATE durable_jobs
                SET heartbeat_at = ?, lease_expires_at = ?, updated_at = ?
                WHERE id = ? AND status = 'leased' AND lease_token = ? AND lease_expires_at > ?
                """,
                (
                    _timestamp(now),
                    _timestamp(now + timedelta(seconds=max(5, lease_seconds))),
                    _timestamp(now),
                    job_id,
                    lease_token,
                    _timestamp(now),
                ),
            )
        return updated.rowcount == 1

    def complete_job(self, job_id: int, lease_token: str, result: dict[str, Any]) -> DurableJob | None:
        now = _utc_now()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                UPDATE durable_jobs
                SET status = 'succeeded', result_json = ?, error_message = NULL,
                    completed_at = ?, lease_owner = NULL, lease_token = NULL,
                    lease_expires_at = NULL, updated_at = ?
                WHERE id = ? AND status = 'leased' AND lease_token = ?
                RETURNING *
                """,
                (_canonical_json(result), _timestamp(now), _timestamp(now), job_id, lease_token),
            ).fetchone()
        return _job_from_row(row) if row else None

    def retry_job(self, job_id: int, lease_token: str, error: str, backoff_seconds: int) -> DurableJob | None:
        now = _utc_now()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT attempts, max_attempts FROM durable_jobs WHERE id = ? AND status = 'leased' AND lease_token = ?",
                (job_id, lease_token),
            ).fetchone()
            if row is None:
                return None
            terminal = int(row["attempts"]) >= int(row["max_attempts"])
            status = "dead_letter" if terminal else "queued"
            completed_at = _timestamp(now) if terminal else None
            connection.execute(
                """
                UPDATE durable_jobs
                SET status = ?, error_message = ?, available_at = ?, completed_at = ?,
                    lease_owner = NULL, lease_token = NULL, lease_expires_at = NULL,
                    heartbeat_at = NULL, updated_at = ?
                WHERE id = ? AND status = 'leased' AND lease_token = ?
                """,
                (
                    status,
                    _safe_error(error),
                    _timestamp(now + timedelta(seconds=max(1, backoff_seconds))),
                    completed_at,
                    _timestamp(now),
                    job_id,
                    lease_token,
                ),
            )
            updated = connection.execute("SELECT * FROM durable_jobs WHERE id = ?", (job_id,)).fetchone()
        return _job_from_row(updated) if updated else None

    def begin_inbox(self, consumer_name: str, event: EventEnvelope) -> InboxDecision:
        payload_hash = hashlib.sha256(_canonical_json(event.payload).encode("utf-8")).hexdigest()
        with connect_database(self.database_path) as connection:
            existing = connection.execute(
                "SELECT status, payload_sha256 FROM inbox_receipts WHERE consumer_name = ? AND event_id = ?",
                (consumer_name, event.event_id),
            ).fetchone()
            if existing is not None:
                if existing["payload_sha256"] != payload_hash:
                    raise ValueError("event_id repetido com payload divergente")
                return InboxDecision(accepted=False, duplicate=True, status=str(existing["status"]))
            connection.execute(
                """
                INSERT INTO inbox_receipts (
                    consumer_name, event_id, event_type, schema_version, payload_sha256
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (consumer_name, event.event_id, event.event_type, event.schema_version, payload_hash),
            )
        return InboxDecision(accepted=True, duplicate=False, status="processing")

    def finish_inbox(self, consumer_name: str, event_id: str, result: dict[str, Any]) -> bool:
        with connect_database(self.database_path) as connection:
            updated = connection.execute(
                """
                UPDATE inbox_receipts
                SET status = 'processed', result_json = ?, error_message = NULL, processed_at = ?
                WHERE consumer_name = ? AND event_id = ? AND status = 'processing'
                """,
                (_canonical_json(result), _timestamp(_utc_now()), consumer_name, event_id),
            )
        return updated.rowcount == 1

    def metrics(self) -> dict[str, dict[str, int]]:
        with connect_database(self.database_path) as connection:
            job_rows = connection.execute(
                "SELECT queue_name, status, COUNT(*) AS total FROM durable_jobs GROUP BY queue_name, status"
            ).fetchall()
            outbox_rows = connection.execute(
                "SELECT status, COUNT(*) AS total FROM outbox_events GROUP BY status"
            ).fetchall()
        jobs = {f"{row['queue_name']}:{row['status']}": int(row["total"]) for row in job_rows}
        outbox = {str(row["status"]): int(row["total"]) for row in outbox_rows}
        return {"jobs": jobs, "outbox": outbox}

    def worker_desired_state(self, queue_name: str) -> str:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT desired_state FROM worker_controls WHERE queue_name = ?",
                (queue_name,),
            ).fetchone()
        return str(row["desired_state"]) if row else "paused"

    def register_worker(
        self,
        worker_id: str,
        queue_name: str,
        release_sha: str,
        concurrency: int,
    ) -> None:
        now = _timestamp(_utc_now())
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO worker_instances (
                    worker_id, queue_name, release_sha, state, concurrency,
                    started_at, heartbeat_at, stopped_at
                ) VALUES (?, ?, ?, 'running', ?, ?, ?, NULL)
                ON CONFLICT(worker_id) DO UPDATE SET
                    queue_name = excluded.queue_name,
                    release_sha = excluded.release_sha,
                    state = 'running',
                    concurrency = excluded.concurrency,
                    started_at = excluded.started_at,
                    heartbeat_at = excluded.heartbeat_at,
                    stopped_at = NULL
                """,
                (worker_id, queue_name, release_sha, concurrency, now, now),
            )

    def heartbeat_worker(self, worker_id: str, state: str = "running") -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                "UPDATE worker_instances SET state = ?, heartbeat_at = ? WHERE worker_id = ?",
                (state, _timestamp(_utc_now()), worker_id),
            )

    def stop_worker(self, worker_id: str) -> None:
        now = _timestamp(_utc_now())
        with connect_database(self.database_path) as connection:
            connection.execute(
                "UPDATE worker_instances SET state = 'stopped', heartbeat_at = ?, stopped_at = ? WHERE worker_id = ?",
                (now, now, worker_id),
            )

    def set_worker_state(self, queue_name: str, desired_state: str, actor: str) -> None:
        if queue_name not in {"outbox", *QUEUE_ACTIVE_LIMITS}:
            raise ValueError("fila desconhecida")
        if desired_state not in {"running", "paused", "draining"}:
            raise ValueError("estado de worker inválido")
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO worker_controls (queue_name, desired_state, max_concurrency, updated_by, updated_at)
                VALUES (?, ?, 1, ?, ?)
                ON CONFLICT(queue_name) DO UPDATE SET
                    desired_state = excluded.desired_state,
                    updated_by = excluded.updated_by,
                    updated_at = excluded.updated_at
                """,
                (queue_name, desired_state, actor[:160], _timestamp(_utc_now())),
            )

    def dead_letter_preview(self, queue_name: str, limit: int = 50) -> list[dict[str, Any]]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, job_key, job_type, attempts, max_attempts, error_message, completed_at
                FROM durable_jobs
                WHERE queue_name = ? AND status = 'dead_letter'
                ORDER BY completed_at DESC, id DESC
                LIMIT ?
                """,
                (queue_name, max(1, min(limit, 100))),
            ).fetchall()
        return [dict(row) for row in rows]

    def replay_dead_letter(
        self,
        job_id: int,
        expected_job_key: str,
        replay_key: str,
        actor: str,
        queue_name: str | None = None,
    ) -> DurableJob:
        with connect_database(self.database_path) as connection:
            statement = "SELECT * FROM durable_jobs WHERE id = ? AND status = 'dead_letter'"
            parameters: tuple[object, ...] = (job_id,)
            if queue_name is not None:
                statement += " AND queue_name = ?"
                parameters = (job_id, queue_name)
            row = connection.execute(statement, parameters).fetchone()
            if row is None:
                raise ValueError("job dead-letter não encontrado")
            if row["job_key"] != expected_job_key:
                raise ValueError("confirmação do job_key não confere")
            existing = connection.execute(
                "SELECT event_id FROM outbox_events WHERE event_id = ?",
                (f"job-replay:{replay_key}",),
            ).fetchone()
            if existing is not None:
                return _job_from_row(row)
            sequence = connection.execute(
                "SELECT COALESCE(MAX(sequence_no), 0) + 1 AS next_sequence FROM outbox_events WHERE ordering_key = ?",
                (f"durable-job-replay:{job_id}",),
            ).fetchone()["next_sequence"]
            self.append_event(
                connection,
                EventEnvelope(
                    event_id=f"job-replay:{replay_key}",
                    aggregate_type="durable_job",
                    aggregate_id=str(job_id),
                    event_type="platform.job.replayed",
                    ordering_key=f"durable-job-replay:{job_id}",
                    sequence_no=int(sequence),
                    payload={"job_id": job_id, "job_type": row["job_type"]},
                    headers={"actor": actor[:160]},
                ),
            )
            connection.execute(
                """
                UPDATE durable_jobs
                SET status = 'queued', attempts = 0, available_at = ?, error_message = NULL,
                    result_json = NULL, completed_at = NULL, lease_owner = NULL,
                    lease_token = NULL, lease_expires_at = NULL, heartbeat_at = NULL,
                    updated_at = ?
                WHERE id = ? AND status = 'dead_letter'
                """,
                (_timestamp(_utc_now()), _timestamp(_utc_now()), job_id),
            )
            updated = connection.execute("SELECT * FROM durable_jobs WHERE id = ?", (job_id,)).fetchone()
        return _job_from_row(updated)

    def _enqueue_job(self, connection: DatabaseConnection, **values: Any) -> DurableJob:
        payload_json = _canonical_json(values["payload"])
        if len(payload_json.encode("utf-8")) > MAX_JOB_PAYLOAD_BYTES:
            raise ValueError("payload do job excede 256 KB")
        existing = connection.execute("SELECT * FROM durable_jobs WHERE job_key = ?", (values["job_key"],)).fetchone()
        if existing is not None:
            if existing["job_type"] != values["job_type"] or existing["payload_json"] != payload_json:
                raise ValueError("job_key repetido com contrato divergente")
            return _job_from_row(existing)
        active = connection.execute(
            "SELECT COUNT(*) AS total FROM durable_jobs WHERE queue_name = ? AND status IN ('queued', 'leased')",
            (values["queue_name"],),
        ).fetchone()
        queue_limit = QUEUE_ACTIVE_LIMITS.get(values["queue_name"], 1_000)
        if int(active["total"]) >= queue_limit:
            raise QueueSaturatedError(f"fila {values['queue_name']} atingiu quota ativa")
        if values["owner_type"] and values["owner_id"]:
            owned = connection.execute(
                """
                SELECT COUNT(*) AS total FROM durable_jobs
                WHERE owner_type = ? AND owner_id = ? AND status IN ('queued', 'leased')
                """,
                (values["owner_type"], values["owner_id"]),
            ).fetchone()
            if int(owned["total"]) >= OWNER_ACTIVE_LIMIT:
                raise QueueSaturatedError("owner atingiu quota de jobs ativos")
        cursor = connection.execute(
            """
            INSERT INTO durable_jobs (
                job_key, queue_name, job_type, schema_version, ordering_key,
                owner_type, owner_id, payload_json, priority, max_attempts, available_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                values["job_key"],
                values["queue_name"],
                values["job_type"],
                values["schema_version"],
                values["ordering_key"],
                values["owner_type"],
                values["owner_id"],
                payload_json,
                max(0, min(int(values["priority"]), 1000)),
                values["max_attempts"],
                _timestamp(values["available_at"] or _utc_now()),
            ),
        )
        row = connection.execute("SELECT * FROM durable_jobs WHERE id = ?", (int(cursor.lastrowid),)).fetchone()
        return _job_from_row(row)

    def _dead_letter_exhausted(self, connection: DatabaseConnection, queue_name: str, now: datetime) -> None:
        connection.execute(
            """
            UPDATE durable_jobs
            SET status = 'dead_letter', completed_at = ?, error_message = 'lease expirado após limite de tentativas',
                lease_owner = NULL, lease_token = NULL, lease_expires_at = NULL, updated_at = ?
            WHERE queue_name = ? AND status = 'leased' AND lease_expires_at <= ? AND attempts >= max_attempts
            """,
            (_timestamp(now), _timestamp(now), queue_name, _timestamp(now)),
        )

    def _dead_letter_exhausted_events(self, connection: DatabaseConnection, now: datetime) -> None:
        connection.execute(
            """
            UPDATE outbox_events
            SET status = 'dead_letter', last_error = 'lease expirado após limite de tentativas',
                lease_owner = NULL, lease_token = NULL, lease_expires_at = NULL, updated_at = ?
            WHERE status = 'publishing' AND lease_expires_at <= ? AND attempts >= max_attempts
            """,
            (_timestamp(now), _timestamp(now)),
        )

    def _publish_event(self, connection: DatabaseConnection, event_id: int, lease_token: str) -> bool:
        now = _timestamp(_utc_now())
        updated = connection.execute(
            """
            UPDATE outbox_events
            SET status = 'published', published_at = ?, last_error = NULL,
                lease_owner = NULL, lease_token = NULL, lease_expires_at = NULL, updated_at = ?
            WHERE id = ? AND status = 'publishing' AND lease_token = ?
            """,
            (now, now, event_id, lease_token),
        )
        return updated.rowcount == 1


def _job_from_row(row) -> DurableJob:
    return DurableJob(
        id=int(row["id"]),
        job_key=str(row["job_key"]),
        queue_name=str(row["queue_name"]),
        job_type=str(row["job_type"]),
        schema_version=int(row["schema_version"]),
        ordering_key=row["ordering_key"],
        owner_type=row["owner_type"],
        owner_id=row["owner_id"],
        payload=json.loads(row["payload_json"] or "{}"),
        priority=int(row["priority"]),
        status=str(row["status"]),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        available_at=str(row["available_at"]),
        lease_owner=row["lease_owner"],
        lease_token=row["lease_token"],
        lease_expires_at=row["lease_expires_at"],
        result=json.loads(row["result_json"]) if row["result_json"] else None,
        error_message=row["error_message"],
    )


def _outbox_from_row(row) -> OutboxEvent:
    return OutboxEvent(
        id=int(row["id"]),
        event_id=str(row["event_id"]),
        aggregate_type=str(row["aggregate_type"]),
        aggregate_id=str(row["aggregate_id"]),
        event_type=str(row["event_type"]),
        schema_version=int(row["schema_version"]),
        ordering_key=str(row["ordering_key"]),
        sequence_no=int(row["sequence_no"]),
        payload=json.loads(row["payload_json"] or "{}"),
        headers=json.loads(row["headers_json"] or "{}"),
        status=str(row["status"]),
        attempts=int(row["attempts"]),
        max_attempts=int(row["max_attempts"]),
        lease_owner=row["lease_owner"],
        lease_token=row["lease_token"],
        lease_expires_at=row["lease_expires_at"],
    )


def _canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")


def _safe_error(value: str) -> str:
    return " ".join(value.replace("\x00", "").split())[:1000]
