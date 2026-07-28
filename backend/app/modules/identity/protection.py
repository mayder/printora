from __future__ import annotations

import hashlib
import json
from typing import Any

from app.auth import hash_token
from app.database import connect_database
from app.modules.identity.contracts import (
    AccountExportResponse,
    AccountRequestRecord,
    AuthSessionRecord,
)


class AccountProtectionService:
    """Owns session control and privacy requests without exposing authentication secrets."""

    def __init__(self, database_path):
        self.database_path = database_path

    def list_sessions(self, user_id: int, current_token: str) -> list[AuthSessionRecord]:
        current_hash = hash_token(current_token)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, token_hash, created_at, last_seen_at, expires_at, revoked_at
                FROM auth_sessions
                WHERE user_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (user_id,),
            ).fetchall()
        return [
            AuthSessionRecord(
                id=int(row["id"]),
                current=str(row["token_hash"]) == current_hash,
                created_at=str(row["created_at"]),
                last_seen_at=row["last_seen_at"],
                expires_at=str(row["expires_at"]),
                revoked_at=row["revoked_at"],
            )
            for row in rows
        ]

    def revoke_session(self, user_id: int, session_id: int) -> bool:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE auth_sessions
                SET revoked_at = COALESCE(revoked_at, CURRENT_TIMESTAMP)
                WHERE id = ? AND user_id = ?
                """,
                (session_id, user_id),
            )
        return cursor.rowcount > 0

    def revoke_all_sessions(self, user_id: int, *, except_token: str | None = None) -> int:
        params: list[object] = [user_id]
        exception = ""
        if except_token:
            exception = " AND token_hash <> ?"
            params.append(hash_token(except_token))
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                f"""
                UPDATE auth_sessions
                SET revoked_at = COALESCE(revoked_at, CURRENT_TIMESTAMP)
                WHERE user_id = ? AND revoked_at IS NULL{exception}
                """,
                tuple(params),
            )
        return max(cursor.rowcount, 0)

    def export_account(self, user_id: int, request_key: str) -> AccountExportResponse:
        data = self._export_payload(user_id)
        canonical = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        with connect_database(self.database_path) as connection:
            existing = self._request_row(connection, user_id, request_key)
            if existing is not None and str(existing["request_type"]) != "export":
                raise ValueError("chave de idempotência já usada por outra operação")
            connection.execute(
                """
                INSERT INTO auth_account_requests (
                    request_key, user_id, request_type, status, artifact_sha256,
                    completed_at, updated_at
                )
                VALUES (?, ?, 'export', 'ready', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(request_key) DO UPDATE SET
                    artifact_sha256 = excluded.artifact_sha256,
                    status = 'ready',
                    failure_code = NULL,
                    completed_at = COALESCE(auth_account_requests.completed_at, CURRENT_TIMESTAMP),
                    updated_at = CURRENT_TIMESTAMP
                WHERE auth_account_requests.user_id = excluded.user_id
                  AND auth_account_requests.request_type = 'export'
                """,
                (request_key, user_id, digest),
            )
            request = self._request_record(self._request_row(connection, user_id, request_key))
        return AccountExportResponse(request=request, data=data)

    def deactivate_account(self, user_id: int, request_key: str) -> AccountRequestRecord:
        with connect_database(self.database_path) as connection:
            existing = self._request_row(connection, user_id, request_key)
            if existing is not None:
                if str(existing["request_type"]) != "deletion":
                    raise ValueError("chave de idempotência já usada por outra operação")
                return self._request_record(existing)
            connection.execute(
                """
                INSERT INTO auth_account_requests (
                    request_key, user_id, request_type, status, effective_at,
                    completed_at, updated_at
                )
                VALUES (?, ?, 'deletion', 'completed', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (request_key, user_id),
            )
            connection.execute(
                """
                UPDATE auth_users
                SET is_active = 0, whatsapp = NULL, telegram = NULL,
                    social_links_json = '{}', mfa_enabled = 0,
                    mfa_secret_protected = NULL, mfa_pending_secret_protected = NULL,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (user_id,),
            )
            connection.execute(
                """
                UPDATE social_profiles
                SET visibility = 'private', location = NULL, social_links_json = '{}',
                    updated_at = CURRENT_TIMESTAMP
                WHERE user_id = ?
                """,
                (user_id,),
            )
            connection.execute(
                """
                UPDATE auth_sessions
                SET revoked_at = COALESCE(revoked_at, CURRENT_TIMESTAMP)
                WHERE user_id = ?
                """,
                (user_id,),
            )
            connection.execute(
                """
                UPDATE auth_step_up_tokens
                SET consumed_at = COALESCE(consumed_at, CURRENT_TIMESTAMP)
                WHERE user_id = ?
                """,
                (user_id,),
            )
            return self._request_record(self._request_row(connection, user_id, request_key))

    def _export_payload(self, user_id: int) -> dict[str, object]:
        with connect_database(self.database_path) as connection:
            user = connection.execute(
                """
                SELECT id, email, display_name, whatsapp, telegram, social_links_json,
                       timezone, mfa_enabled, is_active, created_at, updated_at
                FROM auth_users WHERE id = ?
                """,
                (user_id,),
            ).fetchone()
            if user is None:
                raise ValueError("usuário não encontrado")
            profile = connection.execute(
                """
                SELECT slug, display_name, bio, avatar_url, location, social_links_json,
                       visibility, created_at, updated_at
                FROM social_profiles WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()
            organizations = connection.execute(
                """
                SELECT o.id, o.name, m.role, m.created_at
                FROM auth_organization_members m
                JOIN auth_organizations o ON o.id = m.organization_id
                WHERE m.user_id = ? ORDER BY o.id
                """,
                (user_id,),
            ).fetchall()
            printers = connection.execute(
                """
                SELECT id, name, location, organization_id, created_at, updated_at
                FROM printers WHERE owner_user_id = ? ORDER BY id
                """,
                (user_id,),
            ).fetchall()
            moderation = connection.execute(
                """
                SELECT id, entity_type, entity_id, reason, status, created_at, resolved_at
                FROM social_moderation_reports
                WHERE reporter_user_id = ? ORDER BY id
                """,
                (user_id,),
            ).fetchall()
        return {
            "schema": "printora.account-export/v1",
            "account": self._safe_row(user, json_fields={"social_links_json"}),
            "social_profile": self._safe_row(profile, json_fields={"social_links_json"}) if profile else None,
            "organizations": [self._safe_row(row) for row in organizations],
            "owned_printers": [self._safe_row(row) for row in printers],
            "moderation_reports": [self._safe_row(row) for row in moderation],
        }

    @staticmethod
    def _safe_row(row, *, json_fields: set[str] | None = None) -> dict[str, Any]:
        json_fields = json_fields or set()
        result = dict(row)
        for field in json_fields:
            raw = result.get(field)
            result[field.removesuffix("_json")] = json.loads(raw or "{}")
            result.pop(field, None)
        return result

    @staticmethod
    def _request_row(connection, user_id: int, request_key: str):
        return connection.execute(
            """
            SELECT request_key, request_type, status, artifact_sha256, failure_code,
                   effective_at, retention_until, created_at, updated_at, completed_at
            FROM auth_account_requests
            WHERE user_id = ? AND request_key = ?
            """,
            (user_id, request_key),
        ).fetchone()

    @staticmethod
    def _request_record(row) -> AccountRequestRecord:
        if row is None:
            raise RuntimeError("estado da solicitação não persistido")
        return AccountRequestRecord(**dict(row))
