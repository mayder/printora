from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field

from app.database import connect_database, initialize_database

NotificationType = Literal["comment", "reaction", "solution", "follow", "friend_request", "friend_accept", "content_update", "community_post", "digest"]
NotificationEntityType = Literal["post", "comment", "profile", "library_item", "catalog_variant", "community", "collection", "relationship"]
FollowEntityType = Literal["post", "library_item", "catalog_variant", "community", "collection"]
NotificationStatus = Literal["unread", "read", "archived"]

DEFAULT_NOTIFICATION_TYPES: tuple[NotificationType, ...] = (
    "comment",
    "reaction",
    "solution",
    "follow",
    "friend_request",
    "friend_accept",
    "content_update",
    "community_post",
    "digest",
)


class NotificationPreference(BaseModel):
    notification_type: NotificationType
    in_app_enabled: bool = True
    digest_enabled: bool = False


class NotificationPreferenceUpdate(BaseModel):
    notification_type: NotificationType
    in_app_enabled: bool = True
    digest_enabled: bool = False


class ContentFollowPayload(BaseModel):
    entity_type: FollowEntityType
    entity_id: int = Field(ge=1)
    muted: bool = False
    digest_enabled: bool = False


class ContentFollowRecord(BaseModel):
    id: int
    user_id: int
    entity_type: FollowEntityType
    entity_id: int
    muted: bool
    digest_enabled: bool
    title: str
    created_at: str
    updated_at: str


class SocialNotificationRecord(BaseModel):
    id: int
    recipient_user_id: int
    actor_user_id: int | None
    actor_display_name: str | None = None
    notification_type: NotificationType
    entity_type: NotificationEntityType
    entity_id: int
    title: str
    body: str
    action_url: str | None
    status: NotificationStatus
    metadata: dict[str, object]
    created_at: str
    read_at: str | None


class NotificationCenterResponse(BaseModel):
    notifications: list[SocialNotificationRecord]
    unread_count: int
    preferences: list[NotificationPreference]
    follows: list[ContentFollowRecord]
    digest: list[SocialNotificationRecord]


class SocialNotificationsRepository:
    def __init__(self, database_path):
        self.database_path = database_path

    def ensure_schema(self) -> None:
        initialize_database(self.database_path)

    def notification_center(self, user_id: int, *, status: NotificationStatus | None = None) -> NotificationCenterResponse:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._ensure_preferences(connection, user_id)
            clauses = ["n.recipient_user_id = ?"]
            params: list[object] = [user_id]
            if status:
                clauses.append("n.status = ?")
                params.append(status)
            rows = connection.execute(
                NOTIFICATION_SQL
                + f"""
                WHERE {' AND '.join(clauses)}
                ORDER BY n.created_at DESC, n.id DESC
                LIMIT 80
                """,
                tuple(params),
            ).fetchall()
            unread_count = int(connection.execute("SELECT COUNT(*) AS total FROM social_notifications WHERE recipient_user_id = ? AND status = 'unread'", (user_id,)).fetchone()["total"])
            prefs = connection.execute(
                """
                SELECT notification_type, in_app_enabled, digest_enabled
                FROM social_notification_preferences
                WHERE user_id = ?
                ORDER BY notification_type
                """,
                (user_id,),
            ).fetchall()
            digest_rows = connection.execute(
                NOTIFICATION_SQL
                + """
                JOIN social_notification_preferences pref
                  ON pref.user_id = n.recipient_user_id
                 AND pref.notification_type = n.notification_type
                 AND pref.digest_enabled = 1
                WHERE n.recipient_user_id = ? AND n.status = 'unread'
                ORDER BY n.created_at DESC, n.id DESC
                LIMIT 20
                """,
                (user_id,),
            ).fetchall()
            return NotificationCenterResponse(
                notifications=[_notification_from_row(row) for row in rows],
                unread_count=unread_count,
                preferences=[_preference_from_row(row) for row in prefs],
                follows=self.list_follows(user_id, connection=connection),
                digest=[_notification_from_row(row) for row in digest_rows],
            )

    def update_preference(self, user_id: int, payload: NotificationPreferenceUpdate) -> list[NotificationPreference]:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._ensure_preferences(connection, user_id)
            connection.execute(
                """
                INSERT INTO social_notification_preferences (user_id, notification_type, in_app_enabled, digest_enabled)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, notification_type) DO UPDATE SET
                    in_app_enabled = excluded.in_app_enabled,
                    digest_enabled = excluded.digest_enabled,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, payload.notification_type, 1 if payload.in_app_enabled else 0, 1 if payload.digest_enabled else 0),
            )
            rows = connection.execute(
                "SELECT notification_type, in_app_enabled, digest_enabled FROM social_notification_preferences WHERE user_id = ? ORDER BY notification_type",
                (user_id,),
            ).fetchall()
            return [_preference_from_row(row) for row in rows]

    def follow_content(self, user_id: int, payload: ContentFollowPayload) -> ContentFollowRecord:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            title = self._entity_title(connection, payload.entity_type, payload.entity_id)
            if not title:
                raise ValueError("conteúdo não encontrado para acompanhamento")
            connection.execute(
                """
                INSERT INTO social_content_follows (user_id, entity_type, entity_id, muted, digest_enabled)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, entity_type, entity_id) DO UPDATE SET
                    muted = excluded.muted,
                    digest_enabled = excluded.digest_enabled,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, payload.entity_type, payload.entity_id, 1 if payload.muted else 0, 1 if payload.digest_enabled else 0),
            )
            row = connection.execute("SELECT * FROM social_content_follows WHERE user_id = ? AND entity_type = ? AND entity_id = ?", (user_id, payload.entity_type, payload.entity_id)).fetchone()
            return self._follow_from_row(connection, row)

    def unfollow_content(self, user_id: int, entity_type: FollowEntityType, entity_id: int) -> None:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            connection.execute("DELETE FROM social_content_follows WHERE user_id = ? AND entity_type = ? AND entity_id = ?", (user_id, entity_type, entity_id))

    def list_follows(self, user_id: int, *, connection=None) -> list[ContentFollowRecord]:
        if connection is None:
            self.ensure_schema()
            with connect_database(self.database_path) as managed:
                return self.list_follows(user_id, connection=managed)
        rows = connection.execute(
            """
            SELECT * FROM social_content_follows
            WHERE user_id = ?
            ORDER BY updated_at DESC, id DESC
            LIMIT 80
            """,
            (user_id,),
        ).fetchall()
        return [self._follow_from_row(connection, row) for row in rows]

    def mark_read(self, user_id: int, notification_id: int) -> SocialNotificationRecord:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE social_notifications
                SET status = 'read', read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
                WHERE id = ? AND recipient_user_id = ?
                """,
                (notification_id, user_id),
            )
            row = connection.execute(NOTIFICATION_SQL + "WHERE n.id = ? AND n.recipient_user_id = ?", (notification_id, user_id)).fetchone()
            if row is None:
                raise ValueError("notificação não encontrada")
            return _notification_from_row(row)

    def mark_all_read(self, user_id: int) -> None:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE social_notifications
                SET status = 'read', read_at = COALESCE(read_at, CURRENT_TIMESTAMP)
                WHERE recipient_user_id = ? AND status = 'unread'
                """,
                (user_id,),
            )

    def create_notification(
        self,
        recipient_user_id: int,
        *,
        actor_user_id: int | None,
        notification_type: NotificationType,
        entity_type: NotificationEntityType,
        entity_id: int,
        title: str,
        body: str = "",
        action_url: str | None = None,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            self._create_notification(connection, recipient_user_id, actor_user_id=actor_user_id, notification_type=notification_type, entity_type=entity_type, entity_id=entity_id, title=title, body=body, action_url=action_url, metadata=metadata or {})

    def notify_content_followers(
        self,
        *,
        actor_user_id: int,
        entity_type: FollowEntityType,
        entity_id: int,
        notification_type: NotificationType,
        title: str,
        body: str,
        action_url: str | None,
        extra_recipient_user_ids: set[int] | None = None,
    ) -> None:
        self.ensure_schema()
        with connect_database(self.database_path) as connection:
            recipients = set(extra_recipient_user_ids or set())
            follow_rows = connection.execute(
                """
                SELECT user_id FROM social_content_follows
                WHERE entity_type = ? AND entity_id = ? AND muted = 0
                """,
                (entity_type, entity_id),
            ).fetchall()
            recipients.update(int(row["user_id"]) for row in follow_rows)
            for recipient_id in sorted(recipients):
                self._create_notification(connection, recipient_id, actor_user_id=actor_user_id, notification_type=notification_type, entity_type=entity_type, entity_id=entity_id, title=title, body=body, action_url=action_url, metadata={})

    def _create_notification(self, connection, recipient_user_id: int, *, actor_user_id: int | None, notification_type: NotificationType, entity_type: NotificationEntityType, entity_id: int, title: str, body: str, action_url: str | None, metadata: dict[str, object]) -> None:
        if actor_user_id == recipient_user_id:
            return
        if actor_user_id is not None and self._is_blocked(connection, recipient_user_id, actor_user_id):
            return
        self._ensure_preferences(connection, recipient_user_id)
        pref = connection.execute(
            "SELECT in_app_enabled FROM social_notification_preferences WHERE user_id = ? AND notification_type = ?",
            (recipient_user_id, notification_type),
        ).fetchone()
        if pref is not None and int(pref["in_app_enabled"]) == 0:
            return
        connection.execute(
            """
            INSERT INTO social_notifications (
                recipient_user_id, actor_user_id, notification_type, entity_type,
                entity_id, title, body, action_url, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                recipient_user_id,
                actor_user_id,
                notification_type,
                entity_type,
                entity_id,
                title.strip()[:160],
                body.strip()[:500],
                action_url,
                json.dumps(metadata, ensure_ascii=False, sort_keys=True),
            ),
        )

    def _ensure_preferences(self, connection, user_id: int) -> None:
        for notification_type in DEFAULT_NOTIFICATION_TYPES:
            connection.execute(
                """
                INSERT OR IGNORE INTO social_notification_preferences (user_id, notification_type, in_app_enabled, digest_enabled)
                VALUES (?, ?, 1, ?)
                """,
                (user_id, notification_type, 1 if notification_type == "digest" else 0),
            )

    def _follow_from_row(self, connection, row) -> ContentFollowRecord:
        return ContentFollowRecord(
            id=int(row["id"]),
            user_id=int(row["user_id"]),
            entity_type=row["entity_type"],
            entity_id=int(row["entity_id"]),
            muted=bool(row["muted"]),
            digest_enabled=bool(row["digest_enabled"]),
            title=self._entity_title(connection, row["entity_type"], int(row["entity_id"])) or "Conteúdo indisponível",
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _entity_title(self, connection, entity_type: str, entity_id: int) -> str:
        table_map = {
            "post": ("social_feed_items", "id", "title", "deleted_at IS NULL"),
            "library_item": ("social_library_items", "id", "title", "status = 'active'"),
            "catalog_variant": ("catalog_printer_variants", "id", "name", "trust_state != 'blocked'"),
            "community": ("social_communities", "id", "name", "status IN ('active', 'uncurated')"),
            "collection": ("social_library_collections", "id", "name", "status = 'active'"),
        }
        table, id_column, title_column, predicate = table_map[entity_type]
        row = connection.execute(f"SELECT {title_column} AS title FROM {table} WHERE {id_column} = ? AND {predicate}", (entity_id,)).fetchone()
        return str(row["title"]) if row is not None else ""

    def _is_blocked(self, connection, first_user_id: int, second_user_id: int) -> bool:
        return connection.execute(
            """
            SELECT 1 FROM social_relationships
            WHERE relation_type = 'block' AND status = 'active'
              AND ((actor_user_id = ? AND target_user_id = ?) OR (actor_user_id = ? AND target_user_id = ?))
            """,
            (first_user_id, second_user_id, second_user_id, first_user_id),
        ).fetchone() is not None


NOTIFICATION_SQL = """
SELECT n.*, u.display_name AS actor_display_name
FROM social_notifications n
LEFT JOIN auth_users u ON u.id = n.actor_user_id
"""


def _notification_from_row(row) -> SocialNotificationRecord:
    return SocialNotificationRecord(
        id=int(row["id"]),
        recipient_user_id=int(row["recipient_user_id"]),
        actor_user_id=row["actor_user_id"],
        actor_display_name=row["actor_display_name"],
        notification_type=row["notification_type"],
        entity_type=row["entity_type"],
        entity_id=int(row["entity_id"]),
        title=row["title"],
        body=row["body"],
        action_url=row["action_url"],
        status=row["status"],
        metadata=json.loads(row["metadata_json"] or "{}"),
        created_at=row["created_at"],
        read_at=row["read_at"],
    )


def _preference_from_row(row) -> NotificationPreference:
    return NotificationPreference(
        notification_type=row["notification_type"],
        in_app_enabled=bool(row["in_app_enabled"]),
        digest_enabled=bool(row["digest_enabled"]),
    )
