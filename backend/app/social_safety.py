from __future__ import annotations

import hashlib
import json
from typing import Literal

from pydantic import BaseModel, Field

from app.database import connect_database, initialize_database

FollowersVisibility = Literal["public", "followers", "friends", "private"]
MessagesFrom = Literal["public", "followers", "friends", "none"]
AbuseSignalStatus = Literal["active", "reviewing", "resolved", "dismissed"]


class SocialSafetySettings(BaseModel):
    user_id: int
    profile_discoverable: bool = True
    followers_visibility: FollowersVisibility = "public"
    messages_from: MessagesFrom = "friends"
    allow_content_mentions: bool = True
    allow_download_tracking: bool = True
    updated_at: str


class SocialSafetySettingsUpdate(BaseModel):
    profile_discoverable: bool = True
    followers_visibility: FollowersVisibility = "public"
    messages_from: MessagesFrom = "friends"
    allow_content_mentions: bool = True
    allow_download_tracking: bool = True


class RateLimitResult(BaseModel):
    allowed: bool
    action: str
    remaining: int
    retry_after_seconds: int = 0
    reason: str = ""


class AbuseSignalRecord(BaseModel):
    id: int
    subject_user_id: int | None
    target_user_id: int | None
    action: str
    reason: str
    severity: int
    status: AbuseSignalStatus
    metadata: dict[str, object]
    created_at: str
    updated_at: str
    resolved_at: str | None


class SocialSafetyStatus(BaseModel):
    settings: SocialSafetySettings
    recent_denials: int
    active_signals: list[AbuseSignalRecord]


class SocialSafetyRepository:
    def __init__(self, database_path):
        self.database_path = database_path

    def ensure_schema(self) -> None:
        initialize_database(self.database_path)

    def settings(self, user_id: int) -> SocialSafetySettings:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._ensure_settings(connection, user_id)
            row = connection.execute("SELECT * FROM social_user_safety_settings WHERE user_id = ?", (user_id,)).fetchone()
            return _settings_from_row(row)

    def update_settings(self, user_id: int, payload: SocialSafetySettingsUpdate) -> SocialSafetySettings:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._ensure_settings(connection, user_id)
            connection.execute(
                """
                UPDATE social_user_safety_settings
                SET profile_discoverable = ?, followers_visibility = ?, messages_from = ?,
                    allow_content_mentions = ?, allow_download_tracking = ?, updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (
                    1 if payload.profile_discoverable else 0,
                    payload.followers_visibility,
                    payload.messages_from,
                    1 if payload.allow_content_mentions else 0,
                    1 if payload.allow_download_tracking else 0,
                    user_id,
                ),
            )
            row = connection.execute("SELECT * FROM social_user_safety_settings WHERE user_id = ?", (user_id,)).fetchone()
            self._audit(connection, "safety_settings_updated", user_id, {"fields": list(payload.model_fields_set)})
            return _settings_from_row(row)

    def status(self, user_id: int) -> SocialSafetyStatus:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._ensure_settings(connection, user_id)
            settings = _settings_from_row(connection.execute("SELECT * FROM social_user_safety_settings WHERE user_id = ?", (user_id,)).fetchone())
            denied = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM social_rate_limit_events
                WHERE actor_user_id = ? AND allowed = 0 AND created_at >= datetime('now', '-24 hours')
                """,
                (user_id,),
            ).fetchone()
            signals = connection.execute(
                """
                SELECT * FROM social_abuse_signals
                WHERE subject_user_id = ? AND status IN ('active', 'reviewing')
                ORDER BY severity DESC, created_at DESC, id DESC
                LIMIT 20
                """,
                (user_id,),
            ).fetchall()
            return SocialSafetyStatus(settings=settings, recent_denials=int(denied["total"]), active_signals=[_signal_from_row(row) for row in signals])

    def check_rate_limit(self, *, actor_user_id: int | None, action: str, subject: str, target_user_id: int | None = None) -> RateLimitResult:
        self.ensure_schema()
        limit, window_seconds = _limit_for_action(action)
        subject_hash = hash_subject(subject)
        with connect_database(self.database_path) as connection:
            params: list[object] = [action, f"-{window_seconds} seconds"]
            if actor_user_id is not None:
                actor_clause = "actor_user_id = ?"
                params.append(actor_user_id)
            else:
                actor_clause = "actor_user_id IS NULL AND subject_hash = ?"
                params.append(subject_hash)
            recent = connection.execute(
                f"""
                SELECT COUNT(*) AS total
                FROM social_rate_limit_events
                WHERE action = ? AND created_at >= datetime('now', ?) AND {actor_clause}
                """,
                tuple(params),
            ).fetchone()
            used = int(recent["total"])
            allowed = used < limit
            reason = "" if allowed else "limite temporário de segurança social atingido"
            connection.execute(
                """
                INSERT INTO social_rate_limit_events (actor_user_id, action, subject_hash, allowed, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (actor_user_id, action, subject_hash, 1 if allowed else 0, reason),
            )
            if not allowed:
                self._record_abuse_signal(
                    connection,
                    actor_user_id,
                    target_user_id,
                    action,
                    reason,
                    {"window_seconds": window_seconds, "limit": limit},
                )
            return RateLimitResult(
                allowed=allowed,
                action=action,
                remaining=max(limit - used - 1, 0) if allowed else 0,
                retry_after_seconds=window_seconds if not allowed else 0,
                reason=reason,
            )

    def abuse_signals(self, *, status: AbuseSignalStatus | None = None, limit: int = 80) -> list[AbuseSignalRecord]:
        self.ensure_schema()
        clauses: list[str] = []
        params: list[object] = []
        if status:
            clauses.append("status = ?")
            params.append(status)
        where = "WHERE " + " AND ".join(clauses) if clauses else ""
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                f"""
                SELECT * FROM social_abuse_signals
                {where}
                ORDER BY CASE status WHEN 'active' THEN 0 WHEN 'reviewing' THEN 1 ELSE 2 END,
                         severity DESC, created_at DESC, id DESC
                LIMIT ?
                """,
                (*params, min(max(limit, 1), 200)),
            ).fetchall()
            return [_signal_from_row(row) for row in rows]

    def _ensure_settings(self, connection, user_id: int) -> None:
        connection.execute(
            """
            INSERT OR IGNORE INTO social_user_safety_settings (user_id)
            VALUES (?)
            """,
            (user_id,),
        )

    def _record_abuse_signal(self, connection, subject_user_id: int | None, target_user_id: int | None, action: str, reason: str, metadata: dict[str, object]) -> None:
        actor_clause = "actor_user_id IS NULL" if subject_user_id is None else "actor_user_id = ?"
        params: tuple[object, ...] = (action,) if subject_user_id is None else (subject_user_id, action)
        recent_denials = connection.execute(
            f"""
            SELECT COUNT(*) AS total
            FROM social_rate_limit_events
            WHERE {actor_clause} AND action = ? AND allowed = 0 AND created_at >= datetime('now', '-24 hours')
            """,
            params,
        ).fetchone()
        severity = min(5, 2 + int(recent_denials["total"]) // 3)
        connection.execute(
            """
            INSERT INTO social_abuse_signals (
                subject_user_id, target_user_id, action, reason, severity, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (subject_user_id, target_user_id, action, reason, severity, json.dumps(metadata, ensure_ascii=False, sort_keys=True)),
        )
        self._audit(connection, "abuse_signal", subject_user_id, {"action": action, "severity": severity, "target_user_id": target_user_id})

    def _audit(self, connection, action: str, actor_user_id: int | None, payload: dict[str, object]) -> None:
        connection.execute(
            """
            INSERT INTO catalog_audit_events (entity_type, entity_id, action, actor_user_id, payload_json)
            VALUES ('social_safety', ?, ?, ?, ?)
            """,
            (actor_user_id or 0, action, actor_user_id, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
        )


def hash_subject(subject: str) -> str:
    return hashlib.sha256(subject.strip().lower().encode("utf-8")).hexdigest()


def _limit_for_action(action: str) -> tuple[int, int]:
    return {
        "profile_lookup": (40, 60),
        "profile_search": (30, 60),
        "relationship_action": (20, 600),
        "moderation_report": (10, 3600),
        "library_download": (120, 3600),
        "content_mutation": (50, 600),
    }.get(action, (60, 600))


def _settings_from_row(row) -> SocialSafetySettings:
    return SocialSafetySettings(
        user_id=int(row["user_id"]),
        profile_discoverable=bool(row["profile_discoverable"]),
        followers_visibility=row["followers_visibility"],
        messages_from=row["messages_from"],
        allow_content_mentions=bool(row["allow_content_mentions"]),
        allow_download_tracking=bool(row["allow_download_tracking"]),
        updated_at=row["updated_at"],
    )


def _signal_from_row(row) -> AbuseSignalRecord:
    return AbuseSignalRecord(
        id=int(row["id"]),
        subject_user_id=row["subject_user_id"],
        target_user_id=row["target_user_id"],
        action=row["action"],
        reason=row["reason"],
        severity=int(row["severity"]),
        status=row["status"],
        metadata=json.loads(row["metadata_json"] or "{}"),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        resolved_at=row["resolved_at"],
    )
