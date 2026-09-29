from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.database import connect_database


KEY_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{7,127}$")


@dataclass(frozen=True)
class IdempotencyDecision:
    status: str
    lock_token: str | None = None
    response_status: int | None = None
    response_headers: dict[str, str] | None = None
    response_body: bytes | None = None


class IdempotencyRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def begin(self, scope: str, key: str, request_hash: str) -> IdempotencyDecision:
        if not KEY_PATTERN.fullmatch(key):
            raise ValueError("Idempotency-Key inválida")
        now = _utc_now()
        lock_token = uuid4().hex
        with connect_database(self.database_path) as connection:
            created = connection.execute(
                """
                INSERT INTO idempotency_records (
                    scope, idempotency_key, request_sha256, state, lock_token,
                    lock_expires_at, expires_at, created_at, updated_at
                ) VALUES (?, ?, ?, 'processing', ?, ?, ?, ?, ?)
                ON CONFLICT(scope, idempotency_key) DO NOTHING
                """,
                (
                    scope,
                    key,
                    request_hash,
                    lock_token,
                    _timestamp(now + timedelta(minutes=2)),
                    _timestamp(now + timedelta(hours=24)),
                    _timestamp(now),
                    _timestamp(now),
                ),
            )
            if created.rowcount == 1:
                return IdempotencyDecision(status="acquired", lock_token=lock_token)
            row = connection.execute(
                "SELECT * FROM idempotency_records WHERE scope = ? AND idempotency_key = ?",
                (scope, key),
            ).fetchone()
            if row is None:
                raise RuntimeError("registro idempotente não pôde ser lido")
            if row["request_sha256"] != request_hash:
                return IdempotencyDecision(status="conflict")
            if row["state"] == "completed":
                return IdempotencyDecision(
                    status="replay",
                    response_status=int(row["response_status"]),
                    response_headers=json.loads(row["response_headers_json"] or "{}"),
                    response_body=base64.b64decode(row["response_body_json"] or ""),
                )
            if row["state"] == "processing" and str(row["lock_expires_at"] or "") > _timestamp(now):
                return IdempotencyDecision(status="processing")
            reclaimed = connection.execute(
                """
                UPDATE idempotency_records
                SET state = 'processing', lock_token = ?, lock_expires_at = ?, updated_at = ?
                WHERE scope = ? AND idempotency_key = ?
                  AND request_sha256 = ?
                  AND (state = 'failed' OR lock_expires_at <= ?)
                """,
                (
                    lock_token,
                    _timestamp(now + timedelta(minutes=2)),
                    _timestamp(now),
                    scope,
                    key,
                    request_hash,
                    _timestamp(now),
                ),
            )
        return IdempotencyDecision(
            status="acquired" if reclaimed.rowcount == 1 else "processing",
            lock_token=lock_token if reclaimed.rowcount == 1 else None,
        )

    def complete(
        self,
        scope: str,
        key: str,
        lock_token: str,
        status_code: int,
        headers: dict[str, str],
        body: bytes,
    ) -> bool:
        with connect_database(self.database_path) as connection:
            updated = connection.execute(
                """
                UPDATE idempotency_records
                SET state = 'completed', response_status = ?, response_headers_json = ?,
                    response_body_json = ?, lock_token = NULL, lock_expires_at = NULL, updated_at = ?
                WHERE scope = ? AND idempotency_key = ? AND state = 'processing' AND lock_token = ?
                """,
                (
                    status_code,
                    json.dumps(headers, sort_keys=True),
                    base64.b64encode(body).decode("ascii"),
                    _timestamp(_utc_now()),
                    scope,
                    key,
                    lock_token,
                ),
            )
        return updated.rowcount == 1

    def fail(self, scope: str, key: str, lock_token: str) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE idempotency_records
                SET state = 'failed', lock_token = NULL, lock_expires_at = NULL, updated_at = ?
                WHERE scope = ? AND idempotency_key = ? AND state = 'processing' AND lock_token = ?
                """,
                (_timestamp(_utc_now()), scope, key, lock_token),
            )


def request_fingerprint(method: str, path: str, query: str, body: bytes, content_type: str) -> str:
    digest = hashlib.sha256()
    for value in (method.upper(), path, query, content_type):
        digest.update(value.encode("utf-8"))
        digest.update(b"\x00")
    digest.update(body)
    return digest.hexdigest()


def idempotency_scope(method: str, path: str, authorization: str | None) -> str:
    actor = hashlib.sha256((authorization or "anonymous").encode("utf-8")).hexdigest()[:24]
    return f"http:{actor}:{method.upper()}:{path}"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
