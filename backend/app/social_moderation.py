from __future__ import annotations

import json
import hashlib
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.database import connect_database, initialize_database
from app.modules.platform.durable_execution import DurableExecutionRepository, EventEnvelope

ModerationEntityType = Literal["post", "comment", "profile", "library_item", "catalog_variant", "community", "tag"]
ModerationReason = Literal["spam", "unsafe", "illegal", "harassment", "privacy", "wrong_metadata", "other"]
ModerationReportStatus = Literal["open", "reviewing", "resolved", "dismissed"]
ModerationAction = Literal["mark_reviewing", "hide", "remove", "block", "restore", "dismiss", "curate"]
ModerationAppealStatus = Literal["open", "upheld", "overturned"]


class ModerationReportCreate(BaseModel):
    entity_type: ModerationEntityType
    entity_id: int = Field(ge=1)
    reason: ModerationReason
    detail: str = Field(default="", max_length=1000)

    @field_validator("detail")
    @classmethod
    def clean_detail(cls, value: str) -> str:
        return value.strip()


class ModerationActionPayload(BaseModel):
    action: ModerationAction
    reason: str = Field(min_length=3, max_length=1000)
    status: str | None = Field(default=None, max_length=40)

    @field_validator("reason", "status")
    @classmethod
    def clean_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class ModerationReportRecord(BaseModel):
    id: int
    entity_type: ModerationEntityType
    entity_id: int
    reporter_user_id: int | None
    reporter_display_name: str | None = None
    reason: str
    detail: str
    status: ModerationReportStatus
    assigned_moderator_user_id: int | None
    resolution_note: str | None
    created_at: str
    updated_at: str
    resolved_at: str | None
    entity_title: str | None = None
    entity_status: str | None = None


class ModerationActionRecord(BaseModel):
    id: int
    report_id: int | None
    entity_type: ModerationEntityType
    entity_id: int
    action: str
    previous_state: dict[str, object]
    new_state: dict[str, object]
    moderator_user_id: int | None
    reason: str
    created_at: str


class ModerationQueueResponse(BaseModel):
    reports: list[ModerationReportRecord]
    actions: list[ModerationActionRecord]


class ModerationAppealCreate(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        return value.strip()


class ModerationAppealDecision(BaseModel):
    status: Literal["upheld", "overturned"]
    resolution_note: str = Field(min_length=3, max_length=1000)

    @field_validator("resolution_note")
    @classmethod
    def clean_note(cls, value: str) -> str:
        return value.strip()


class ModerationAppealRecord(BaseModel):
    id: int
    report_id: int
    appellant_user_id: int
    reason: str
    status: ModerationAppealStatus
    reviewed_by_user_id: int | None
    resolution_note: str | None
    retention_until: str
    created_at: str
    updated_at: str
    resolved_at: str | None


class SocialModerationRepository:
    def __init__(self, database_path):
        self.database_path = database_path

    def ensure_schema(self) -> None:
        initialize_database(self.database_path)

    def create_report(self, reporter_user_id: int, payload: ModerationReportCreate) -> ModerationReportRecord:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._ensure_reportable_entity(connection, payload.entity_type, payload.entity_id)
            connection.execute(
                """
                INSERT INTO social_moderation_reports (
                    entity_type, entity_id, reporter_user_id, reason, detail
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(entity_type, entity_id, reporter_user_id, reason)
                DO NOTHING
                """,
                (payload.entity_type, payload.entity_id, reporter_user_id, payload.reason, payload.detail),
            )
            report_id = connection.execute(
                """
                SELECT id FROM social_moderation_reports
                WHERE entity_type = ? AND entity_id = ? AND reporter_user_id = ? AND reason = ?
                """,
                (payload.entity_type, payload.entity_id, reporter_user_id, payload.reason),
            ).fetchone()["id"]
            event_payload = {
                "entity_type": payload.entity_type,
                "entity_id": payload.entity_id,
                "reason": payload.reason,
                "detail": payload.detail,
            }
            payload_digest = hashlib.sha256(
                json.dumps(event_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
            sequence = connection.execute(
                "SELECT COALESCE(MAX(sequence_no), 0) + 1 AS value FROM outbox_events WHERE ordering_key = ?",
                (f"moderation-report:{report_id}",),
            ).fetchone()["value"]
            DurableExecutionRepository(self.database_path).append_event(
                connection,
                EventEnvelope(
                    event_id=f"moderation-report:{report_id}:{payload_digest[:24]}",
                    aggregate_type="moderation_report",
                    aggregate_id=str(report_id),
                    event_type="moderation.report.created",
                    ordering_key=f"moderation-report:{report_id}",
                    sequence_no=int(sequence),
                    payload=event_payload,
                    headers={"purpose": "safety_moderation", "sanitization": "transient-context-v1"},
                ),
            )
            self._audit(connection, "report", payload.entity_type, payload.entity_id, reporter_user_id, {"report_id": report_id, "reason": payload.reason})
            return self._report_by_id(connection, int(report_id))

    def queue(self, *, status: ModerationReportStatus | None = None, limit: int = 50) -> ModerationQueueResponse:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            clauses: list[str] = []
            params: list[object] = []
            if status:
                clauses.append("r.status = ?")
                params.append(status)
            where = "WHERE " + " AND ".join(clauses) if clauses else ""
            rows = connection.execute(
                f"""
                SELECT r.*, u.display_name AS reporter_display_name
                FROM social_moderation_reports r
                LEFT JOIN auth_users u ON u.id = r.reporter_user_id
                {where}
                ORDER BY CASE r.status WHEN 'open' THEN 0 WHEN 'reviewing' THEN 1 ELSE 2 END,
                         r.created_at DESC, r.id DESC
                LIMIT ?
                """,
                (*params, min(max(limit, 1), 100)),
            ).fetchall()
            actions = connection.execute(
                """
                SELECT * FROM social_moderation_actions
                ORDER BY created_at DESC, id DESC
                LIMIT 50
                """
            ).fetchall()
            return ModerationQueueResponse(
                reports=[self._report_from_row(connection, row) for row in rows],
                actions=[_action_from_row(row) for row in actions],
            )

    def apply_action(self, report_id: int, moderator_user_id: int, payload: ModerationActionPayload) -> ModerationReportRecord:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            report = self._report_row(connection, report_id)
            if report is None:
                raise ValueError("denúncia não encontrada")
            entity_type = report["entity_type"]
            entity_id = int(report["entity_id"])
            previous = self._entity_state(connection, entity_type, entity_id)
            new_state = self._apply_entity_action(connection, entity_type, entity_id, payload)
            connection.execute(
                """
                INSERT INTO social_moderation_actions (
                    report_id, entity_type, entity_id, action, previous_state_json,
                    new_state_json, moderator_user_id, reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    entity_type,
                    entity_id,
                    payload.action,
                    json.dumps(previous, ensure_ascii=False, sort_keys=True),
                    json.dumps(new_state, ensure_ascii=False, sort_keys=True),
                    moderator_user_id,
                    payload.reason,
                ),
            )
            next_status = "dismissed" if payload.action == "dismiss" else "resolved"
            if payload.action == "mark_reviewing":
                next_status = "reviewing"
            connection.execute(
                """
                UPDATE social_moderation_reports
                SET status = ?, assigned_moderator_user_id = ?, resolution_note = ?,
                    resolved_at = CASE WHEN ? IN ('resolved', 'dismissed') THEN CURRENT_TIMESTAMP ELSE resolved_at END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (next_status, moderator_user_id, payload.reason, next_status, report_id),
            )
            self._audit(connection, payload.action, entity_type, entity_id, moderator_user_id, {"report_id": report_id, "reason": payload.reason, "state": new_state})
            return self._report_by_id(connection, report_id)

    def create_appeal(
        self,
        report_id: int,
        appellant_user_id: int,
        payload: ModerationAppealCreate,
    ) -> ModerationAppealRecord:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            report = self._report_row(connection, report_id)
            if report is None:
                raise ValueError("denúncia não encontrada")
            if str(report["status"]) not in {"resolved", "dismissed"}:
                raise ValueError("recurso disponível somente após decisão")
            if not self._is_entity_owner(
                connection,
                str(report["entity_type"]),
                int(report["entity_id"]),
                appellant_user_id,
            ):
                raise PermissionError("recurso permitido somente ao responsável pelo conteúdo")
            connection.execute(
                """
                INSERT INTO social_moderation_appeals (report_id, appellant_user_id, reason)
                VALUES (?, ?, ?)
                ON CONFLICT(report_id, appellant_user_id) DO UPDATE SET
                    reason = excluded.reason,
                    status = 'open',
                    reviewed_by_user_id = NULL,
                    resolution_note = NULL,
                    resolved_at = NULL,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (report_id, appellant_user_id, payload.reason),
            )
            row = connection.execute(
                """
                SELECT * FROM social_moderation_appeals
                WHERE report_id = ? AND appellant_user_id = ?
                """,
                (report_id, appellant_user_id),
            ).fetchone()
            self._audit(
                connection,
                "appeal",
                str(report["entity_type"]),
                int(report["entity_id"]),
                appellant_user_id,
                {"report_id": report_id},
            )
            return ModerationAppealRecord(**dict(row))

    def list_appeals(self, status: ModerationAppealStatus | None = None) -> list[ModerationAppealRecord]:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            if status is None:
                rows = connection.execute(
                    "SELECT * FROM social_moderation_appeals ORDER BY created_at, id"
                ).fetchall()
            else:
                rows = connection.execute(
                    """
                    SELECT * FROM social_moderation_appeals
                    WHERE status = ? ORDER BY created_at, id
                    """,
                    (status,),
                ).fetchall()
        return [ModerationAppealRecord(**dict(row)) for row in rows]

    def decide_appeal(
        self,
        appeal_id: int,
        reviewer_user_id: int,
        payload: ModerationAppealDecision,
    ) -> ModerationAppealRecord:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT * FROM social_moderation_appeals WHERE id = ?",
                (appeal_id,),
            ).fetchone()
            if row is None:
                raise ValueError("recurso não encontrado")
            if str(row["status"]) != "open":
                if str(row["status"]) == payload.status:
                    return ModerationAppealRecord(**dict(row))
                raise ValueError("recurso já decidido")
            report = self._report_row(connection, int(row["report_id"]))
            if report is None:
                raise ValueError("denúncia não encontrada")
            if payload.status == "overturned":
                entity_type = str(report["entity_type"])
                entity_id = int(report["entity_id"])
                previous = self._entity_state(connection, entity_type, entity_id)
                restored = self._apply_entity_action(
                    connection,
                    entity_type,
                    entity_id,
                    ModerationActionPayload(
                        action="restore",
                        reason=payload.resolution_note,
                    ),
                )
                connection.execute(
                    """
                    INSERT INTO social_moderation_actions (
                        report_id, entity_type, entity_id, action, previous_state_json,
                        new_state_json, moderator_user_id, reason
                    )
                    VALUES (?, ?, ?, 'restore', ?, ?, ?, ?)
                    """,
                    (
                        int(row["report_id"]),
                        entity_type,
                        entity_id,
                        json.dumps(previous, ensure_ascii=False, sort_keys=True),
                        json.dumps(restored, ensure_ascii=False, sort_keys=True),
                        reviewer_user_id,
                        payload.resolution_note,
                    ),
                )
                self._audit(
                    connection,
                    "appeal_overturned",
                    entity_type,
                    entity_id,
                    reviewer_user_id,
                    {"appeal_id": appeal_id, "state": restored},
                )
            connection.execute(
                """
                UPDATE social_moderation_appeals
                SET status = ?, reviewed_by_user_id = ?, resolution_note = ?,
                    resolved_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'open'
                """,
                (payload.status, reviewer_user_id, payload.resolution_note, appeal_id),
            )
            updated = connection.execute(
                "SELECT * FROM social_moderation_appeals WHERE id = ?",
                (appeal_id,),
            ).fetchone()
            return ModerationAppealRecord(**dict(updated))

    @staticmethod
    def _is_entity_owner(connection, entity_type: str, entity_id: int, user_id: int) -> bool:
        owner_queries = {
            "post": "SELECT 1 FROM social_feed_items WHERE id = ? AND author_user_id = ?",
            "comment": "SELECT 1 FROM social_discussion_comments WHERE id = ? AND author_user_id = ?",
            "profile": "SELECT 1 FROM social_profiles WHERE user_id = ? AND user_id = ?",
            "library_item": "SELECT 1 FROM social_library_items WHERE id = ? AND owner_user_id = ?",
        }
        query = owner_queries.get(entity_type)
        return bool(query and connection.execute(query, (entity_id, user_id)).fetchone())

    def _apply_entity_action(self, connection, entity_type: str, entity_id: int, payload: ModerationActionPayload) -> dict[str, object]:
        action = payload.action
        if action == "mark_reviewing":
            return self._entity_state(connection, entity_type, entity_id)
        if action == "dismiss":
            return self._entity_state(connection, entity_type, entity_id)
        if entity_type == "post":
            if action in {"hide", "remove", "block"}:
                visibility = "private" if action == "hide" else "public"
                connection.execute("UPDATE social_feed_items SET visibility = ?, deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (visibility, entity_id))
            elif action == "restore":
                connection.execute("UPDATE social_feed_items SET visibility = 'public', deleted_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (entity_id,))
        elif entity_type == "comment":
            if action in {"hide", "remove", "block"}:
                connection.execute("UPDATE social_discussion_comments SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (entity_id,))
            elif action == "restore":
                connection.execute("UPDATE social_discussion_comments SET deleted_at = NULL, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (entity_id,))
        elif entity_type == "profile":
            if action in {"hide", "block"}:
                connection.execute("UPDATE social_profiles SET visibility = 'private', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (entity_id,))
            elif action == "restore":
                connection.execute("UPDATE social_profiles SET visibility = 'public', updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (entity_id,))
        elif entity_type == "library_item":
            if action in {"hide", "remove", "block"}:
                connection.execute("UPDATE social_library_items SET status = 'archived', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (entity_id,))
            elif action == "restore":
                connection.execute("UPDATE social_library_items SET status = 'active', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (entity_id,))
        elif entity_type == "catalog_variant":
            if payload.action == "curate" and payload.status:
                state = payload.status
            elif action == "block":
                state = "blocked"
            elif action in {"hide", "remove"}:
                state = "obsolete"
            elif action == "restore":
                state = "community"
            else:
                state = "draft"
            if state not in {"official", "community", "draft", "obsolete", "blocked"}:
                raise ValueError("estado de catálogo inválido")
            connection.execute("UPDATE catalog_printer_variants SET trust_state = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (state, entity_id))
        elif entity_type == "community":
            state = payload.status if payload.action == "curate" and payload.status else "obsolete" if action in {"hide", "remove", "block"} else "active"
            if state not in {"active", "uncurated", "obsolete", "merged"}:
                raise ValueError("estado de comunidade inválido")
            connection.execute("UPDATE social_communities SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (state, entity_id))
        elif entity_type == "tag":
            state = payload.status if payload.action == "curate" and payload.status else "blocked" if action in {"hide", "remove", "block"} else "active"
            if state not in {"active", "curated", "blocked"}:
                raise ValueError("estado de tag inválido")
            connection.execute("UPDATE social_content_tags SET status = ?, source = 'curation', updated_at = CURRENT_TIMESTAMP WHERE id = ?", (state, entity_id))
        else:
            raise ValueError("tipo de entidade não suportado")
        return self._entity_state(connection, entity_type, entity_id)

    def _ensure_entity_exists(self, connection, entity_type: str, entity_id: int) -> None:
        if not self._entity_state(connection, entity_type, entity_id):
            raise ValueError("entidade não encontrada")

    def _ensure_reportable_entity(self, connection, entity_type: str, entity_id: int) -> None:
        queries = {
            "post": """
                SELECT 1 FROM social_feed_items
                WHERE id = ? AND visibility = 'public' AND deleted_at IS NULL
            """,
            "comment": """
                SELECT 1
                FROM social_discussion_comments c
                JOIN social_feed_items p ON p.id = c.feed_item_id
                WHERE c.id = ? AND c.deleted_at IS NULL
                  AND p.visibility = 'public' AND p.deleted_at IS NULL
            """,
            "profile": """
                SELECT 1 FROM social_profiles
                WHERE user_id = ? AND visibility = 'public'
            """,
            "library_item": """
                SELECT 1 FROM social_library_items
                WHERE id = ? AND status = 'active' AND visibility = 'public'
            """,
        }
        query = queries.get(entity_type)
        if query is not None:
            if connection.execute(query, (entity_id,)).fetchone() is None:
                raise ValueError("entidade não encontrada")
            return
        self._ensure_entity_exists(connection, entity_type, entity_id)

    def _entity_state(self, connection, entity_type: str, entity_id: int) -> dict[str, object]:
        table_map = {
            "post": ("social_feed_items", "id", "title", "visibility", "deleted_at"),
            "comment": ("social_discussion_comments", "id", "body", None, "deleted_at"),
            "profile": ("social_profiles", "user_id", "display_name", "visibility", None),
            "library_item": ("social_library_items", "id", "title", "status", None),
            "catalog_variant": ("catalog_printer_variants", "id", "name", "trust_state", None),
            "community": ("social_communities", "id", "name", "status", None),
            "tag": ("social_content_tags", "id", "label", "status", None),
        }
        table, id_column, title_column, state_column, deleted_column = table_map[entity_type]
        row = connection.execute(f"SELECT * FROM {table} WHERE {id_column} = ?", (entity_id,)).fetchone()
        if row is None:
            return {}
        state = row[state_column] if state_column else "active"
        if deleted_column and row[deleted_column] is not None:
            state = "removed"
        return {"title": str(row[title_column] or ""), "state": state}

    def _report_row(self, connection, report_id: int):
        return connection.execute("SELECT * FROM social_moderation_reports WHERE id = ?", (report_id,)).fetchone()

    def _report_by_id(self, connection, report_id: int) -> ModerationReportRecord:
        row = connection.execute(
            """
            SELECT r.*, u.display_name AS reporter_display_name
            FROM social_moderation_reports r
            LEFT JOIN auth_users u ON u.id = r.reporter_user_id
            WHERE r.id = ?
            """,
            (report_id,),
        ).fetchone()
        if row is None:
            raise ValueError("denúncia não encontrada")
        return self._report_from_row(connection, row)

    def _report_from_row(self, connection, row) -> ModerationReportRecord:
        entity_state = self._entity_state(connection, row["entity_type"], int(row["entity_id"]))
        return ModerationReportRecord(
            id=int(row["id"]),
            entity_type=row["entity_type"],
            entity_id=int(row["entity_id"]),
            reporter_user_id=row["reporter_user_id"],
            reporter_display_name=row["reporter_display_name"],
            reason=row["reason"],
            detail=row["detail"],
            status=row["status"],
            assigned_moderator_user_id=row["assigned_moderator_user_id"],
            resolution_note=row["resolution_note"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            resolved_at=row["resolved_at"],
            entity_title=str(entity_state.get("title") or ""),
            entity_status=str(entity_state.get("state") or ""),
        )

    def _audit(self, connection, action: str, entity_type: str, entity_id: int, actor_user_id: int, payload: dict[str, object]) -> None:
        connection.execute(
            """
            INSERT INTO catalog_audit_events (entity_type, entity_id, action, actor_user_id, payload_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (f"social_moderation_{entity_type}", entity_id, action, actor_user_id, json.dumps(payload, ensure_ascii=False, sort_keys=True)),
        )


def _action_from_row(row) -> ModerationActionRecord:
    return ModerationActionRecord(
        id=int(row["id"]),
        report_id=row["report_id"],
        entity_type=row["entity_type"],
        entity_id=int(row["entity_id"]),
        action=row["action"],
        previous_state=json.loads(row["previous_state_json"] or "{}"),
        new_state=json.loads(row["new_state_json"] or "{}"),
        moderator_user_id=row["moderator_user_id"],
        reason=row["reason"],
        created_at=row["created_at"],
    )
