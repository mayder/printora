from __future__ import annotations

from dataclasses import dataclass
import base64
from contextvars import ContextVar
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
import secrets

from app.database import connect_database
from app.modules.identity.application import (
    complete_mfa_login,
    login,
    setup_mfa,
    validate_step_up,
)
from app.modules.identity.contracts import (
    AgentCredentialCreateRequest,
    AgentCredentialRecord,
    AgentCredentialResponse,
    AuthOrganization,
    AuthOrganizationDetail,
    AuthOrganizationInvite,
    AuthOrganizationMember,
    AuthOrganizationPrinter,
    AuthSessionResponse,
    AuthUser,
    CurrentUser,
    LoginRequest,
    LoginResponse,
    MfaCodeRequest,
    MfaLoginRequest,
    MfaSetupResponse,
    OrganizationCreateRequest,
    OrganizationInviteCreateRequest,
    OrganizationMemberAddRequest,
    OrganizationPrinterLinkRequest,
    OrganizationUpdateRequest,
    StepUpRequest,
    StepUpResponse,
    UserPasswordUpdateRequest,
    UserProfileUpdateRequest,
    UserRegisterRequest,
    clean_email,
    clean_optional_text,
    clean_timezone,
)
from app.modules.identity.security import hash_password, totp_code, verify_password, verify_totp
from app.platform_access import is_platform_admin


SESSION_TTL = timedelta(hours=12)
MFA_CHALLENGE_TTL = timedelta(minutes=5)
STEP_UP_TTL = timedelta(minutes=15)
CURRENT_AUTH_USER_ID: ContextVar[int | None] = ContextVar("current_auth_user_id", default=None)
CURRENT_AUTH_ORGANIZATION_IDS: ContextVar[tuple[int, ...]] = ContextVar(
    "current_auth_organization_ids",
    default=(),
)


def set_current_auth_context(user: AuthUser | None) -> None:
    if user is None:
        CURRENT_AUTH_USER_ID.set(None)
        CURRENT_AUTH_ORGANIZATION_IDS.set(())
        return
    CURRENT_AUTH_USER_ID.set(user.id)
    CURRENT_AUTH_ORGANIZATION_IDS.set(tuple(organization.id for organization in user.organizations))


def current_auth_scope() -> tuple[int | None, tuple[int, ...]]:
    return CURRENT_AUTH_USER_ID.get(), CURRENT_AUTH_ORGANIZATION_IDS.get()


def scoped_where_clause(table_alias: str, user_id: int | None, organization_ids: tuple[int, ...]) -> tuple[str, tuple[object, ...]]:
    if user_id is None:
        return "WHERE 1 = 0", ()
    params: list[object] = [user_id]
    clauses = [f"{table_alias}.owner_user_id = ?"]
    if organization_ids:
        placeholders = ", ".join("?" for _ in organization_ids)
        clauses.append(f"{table_alias}.organization_id IN ({placeholders})")
        params.extend(organization_ids)
    return "WHERE (" + " OR ".join(clauses) + ")", tuple(params)


@dataclass(frozen=True)
class AuthRepository:
    database_path: Path

    def create_user(self, payload: UserRegisterRequest) -> AuthUser:
        with connect_database(self.database_path) as connection:
            try:
                cursor = connection.execute(
                    """
                    INSERT INTO auth_users (
                        email, password_hash, display_name, whatsapp, telegram, social_links_json, timezone
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload.email.lower(),
                        hash_password(payload.password),
                        payload.display_name,
                        payload.whatsapp,
                        payload.telegram,
                        payload.social_links.model_dump_json(),
                        payload.timezone,
                    ),
                )
            except Exception as exc:
                raise ValueError("email já cadastrado") from exc
            user_id = int(cursor.lastrowid)
        user = self.get_user(user_id)
        if user is None:
            raise RuntimeError("usuário não foi persistido")
        return user

    def get_user(self, user_id: int) -> AuthUser | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute("SELECT * FROM auth_users WHERE id = ?", (user_id,)).fetchone()
            if row is None:
                return None
            organizations = self._list_user_organizations(connection, user_id)
        return _user_from_row(row, organizations)

    def get_user_by_email(self, email: str) -> AuthUser | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute("SELECT * FROM auth_users WHERE email = ?", (email.lower(),)).fetchone()
            if row is None:
                return None
            organizations = self._list_user_organizations(connection, int(row["id"]))
        return _user_from_row(row, organizations)

    def get_password_hash(self, user_id: int) -> str | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute("SELECT password_hash FROM auth_users WHERE id = ?", (user_id,)).fetchone()
        return str(row["password_hash"]) if row else None

    def update_user_profile(self, user_id: int, payload: UserProfileUpdateRequest) -> AuthUser:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE auth_users
                SET display_name = ?, whatsapp = ?, telegram = ?, social_links_json = ?, timezone = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    payload.display_name,
                    payload.whatsapp,
                    payload.telegram,
                    payload.social_links.model_dump_json(),
                    payload.timezone,
                    user_id,
                ),
            )
        user = self.get_user(user_id)
        if user is None:
            raise ValueError("usuário não encontrado")
        return user

    def update_user_password(self, user_id: int, payload: UserPasswordUpdateRequest) -> None:
        current_hash = self.get_password_hash(user_id)
        if current_hash is None or not verify_password(payload.current_password, current_hash):
            raise ValueError("senha atual inválida")
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE auth_users
                SET password_hash = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (hash_password(payload.new_password), user_id),
            )

    def create_session(self, user_id: int) -> tuple[str, str]:
        token = new_secret("ptr_sess")
        expires_at = utc_now() + SESSION_TTL
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO auth_sessions (user_id, token_hash, expires_at)
                VALUES (?, ?, ?)
                """,
                (user_id, hash_token(token), format_dt(expires_at)),
            )
        return token, format_dt(expires_at)

    def get_user_by_session(self, token: str) -> AuthUser | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT u.*
                FROM auth_sessions s
                JOIN auth_users u ON u.id = s.user_id
                WHERE s.token_hash = ?
                  AND s.revoked_at IS NULL
                  AND s.expires_at > CURRENT_TIMESTAMP
                  AND u.is_active = 1
                """,
                (hash_token(token),),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                "UPDATE auth_sessions SET last_seen_at = CURRENT_TIMESTAMP WHERE token_hash = ?",
                (hash_token(token),),
            )
            organizations = self._list_user_organizations(connection, int(row["id"]))
        return _user_from_row(row, organizations)

    def revoke_session(self, token: str) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE auth_sessions
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE token_hash = ? AND revoked_at IS NULL
                """,
                (hash_token(token),),
            )

    def create_mfa_challenge(self, user_id: int) -> str:
        token = new_secret("ptr_mfa")
        expires_at = utc_now() + MFA_CHALLENGE_TTL
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO auth_mfa_challenges (user_id, challenge_hash, expires_at)
                VALUES (?, ?, ?)
                """,
                (user_id, hash_token(token), format_dt(expires_at)),
            )
        return token

    def consume_mfa_challenge(self, challenge_token: str) -> AuthUser | None:
        token_hash = hash_token(challenge_token)
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT u.*
                FROM auth_mfa_challenges c
                JOIN auth_users u ON u.id = c.user_id
                WHERE c.challenge_hash = ?
                  AND c.consumed_at IS NULL
                  AND c.expires_at > CURRENT_TIMESTAMP
                  AND u.is_active = 1
                """,
                (token_hash,),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                "UPDATE auth_mfa_challenges SET consumed_at = CURRENT_TIMESTAMP WHERE challenge_hash = ?",
                (token_hash,),
            )
            organizations = self._list_user_organizations(connection, int(row["id"]))
        return _user_from_row(row, organizations)

    def get_mfa_secret(self, user_id: int) -> str | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT mfa_secret_protected FROM auth_users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if row is None or not row["mfa_secret_protected"]:
            return None
        return unprotect_secret(self.database_path, str(row["mfa_secret_protected"]))

    def set_mfa_secret(self, user_id: int, secret: str, enabled: bool) -> None:
        protected = protect_secret(self.database_path, secret) if secret else None
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE auth_users
                SET mfa_secret_protected = ?, mfa_pending_secret_protected = NULL,
                    mfa_enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (protected, 1 if enabled else 0, user_id),
            )

    def get_pending_mfa_secret(self, user_id: int) -> str | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                "SELECT mfa_pending_secret_protected FROM auth_users WHERE id = ?",
                (user_id,),
            ).fetchone()
        if row is None or not row["mfa_pending_secret_protected"]:
            return None
        return unprotect_secret(self.database_path, str(row["mfa_pending_secret_protected"]))

    def set_pending_mfa_secret(self, user_id: int, secret: str) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE auth_users
                SET mfa_pending_secret_protected = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (protect_secret(self.database_path, secret), user_id),
            )

    def activate_pending_mfa_secret(self, user_id: int) -> bool:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                UPDATE auth_users
                SET mfa_secret_protected = mfa_pending_secret_protected,
                    mfa_pending_secret_protected = NULL,
                    mfa_enabled = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND mfa_pending_secret_protected IS NOT NULL
                """,
                (user_id,),
            )
        return cursor.rowcount > 0

    def set_mfa_enabled(self, user_id: int, enabled: bool) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE auth_users
                SET mfa_enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (1 if enabled else 0, user_id),
            )

    def create_organization(self, user_id: int, payload: OrganizationCreateRequest) -> AuthOrganization:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                "INSERT INTO auth_organizations (name, owner_user_id) VALUES (?, ?)",
                (payload.name, user_id),
            )
            organization_id = int(cursor.lastrowid)
            connection.execute(
                """
                INSERT INTO auth_organization_members (organization_id, user_id, role)
                VALUES (?, ?, 'owner')
                """,
                (organization_id, user_id),
            )
            row = connection.execute(
                """
                SELECT o.id, o.name, o.owner_user_id, m.role
                FROM auth_organizations o
                JOIN auth_organization_members m ON m.organization_id = o.id
                WHERE o.id = ? AND m.user_id = ?
                """,
                (organization_id, user_id),
            ).fetchone()
        return _organization_from_row(row)

    def update_organization(self, actor_user_id: int, organization_id: int, payload: OrganizationUpdateRequest) -> AuthOrganization:
        with connect_database(self.database_path) as connection:
            self._require_org_owner(connection, organization_id, actor_user_id, "editar organização")
            connection.execute(
                """
                UPDATE auth_organizations
                SET name = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (payload.name, organization_id),
            )
            row = connection.execute(
                """
                SELECT o.id, o.name, o.owner_user_id, m.role
                FROM auth_organizations o
                JOIN auth_organization_members m ON m.organization_id = o.id
                WHERE o.id = ? AND m.user_id = ?
                """,
                (organization_id, actor_user_id),
            ).fetchone()
        return _organization_from_row(row)

    def delete_organization(self, actor_user_id: int, organization_id: int) -> None:
        with connect_database(self.database_path) as connection:
            self._require_org_owner(connection, organization_id, actor_user_id, "excluir organização")
            connection.execute("DELETE FROM auth_organization_printers WHERE organization_id = ?", (organization_id,))
            connection.execute(
                """
                UPDATE auth_organization_invites
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE organization_id = ? AND revoked_at IS NULL AND accepted_at IS NULL
                """,
                (organization_id,),
            )
            connection.execute("DELETE FROM auth_organization_members WHERE organization_id = ?", (organization_id,))
            connection.execute("DELETE FROM auth_organizations WHERE id = ?", (organization_id,))

    def add_organization_member(
        self,
        actor_user_id: int,
        organization_id: int,
        payload: OrganizationMemberAddRequest,
    ) -> AuthOrganization:
        with connect_database(self.database_path) as connection:
            actor_role = self._member_role(connection, organization_id, actor_user_id)
            if actor_role not in ("owner", "admin"):
                raise PermissionError("usuário sem permissão para vincular membros")
            if payload.role == "owner":
                raise PermissionError("transferência de owner exige fluxo dedicado")
            user_row = connection.execute(
                "SELECT id FROM auth_users WHERE email = ? AND is_active = 1",
                (payload.email.lower(),),
            ).fetchone()
            if user_row is None:
                raise ValueError("usuário não encontrado")
            target_user_id = int(user_row["id"])
            connection.execute(
                """
                INSERT INTO auth_organization_members (organization_id, user_id, role)
                VALUES (?, ?, ?)
                ON CONFLICT(organization_id, user_id) DO UPDATE SET
                    role = excluded.role,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (organization_id, target_user_id, payload.role),
            )
            row = connection.execute(
                """
                SELECT o.id, o.name, o.owner_user_id, m.role
                FROM auth_organizations o
                JOIN auth_organization_members m ON m.organization_id = o.id
                WHERE o.id = ? AND m.user_id = ?
                """,
                (organization_id, target_user_id),
            ).fetchone()
        return _organization_from_row(row)

    def organization_detail(self, actor_user_id: int, organization_id: int, base_url: str) -> AuthOrganizationDetail:
        with connect_database(self.database_path) as connection:
            actor_role = self._member_role(connection, organization_id, actor_user_id)
            if actor_role is None:
                raise PermissionError("usuário sem acesso à organização")
            organization = connection.execute(
                """
                SELECT o.id, o.name, o.owner_user_id, m.role
                FROM auth_organizations o
                JOIN auth_organization_members m ON m.organization_id = o.id
                WHERE o.id = ? AND m.user_id = ?
                """,
                (organization_id, actor_user_id),
            ).fetchone()
            members = connection.execute(
                """
                SELECT u.id AS user_id, u.email, u.display_name, m.role, m.created_at
                FROM auth_organization_members m
                JOIN auth_users u ON u.id = m.user_id
                WHERE m.organization_id = ?
                ORDER BY m.role = 'owner' DESC, u.email ASC
                """,
                (organization_id,),
            ).fetchall()
            printers = connection.execute(
                """
                SELECT p.id AS printer_id, p.name, p.moonraker_url, op.created_at AS linked_at
                FROM auth_organization_printers op
                JOIN printers p ON p.id = op.printer_id
                WHERE op.organization_id = ?
                ORDER BY p.name ASC
                """,
                (organization_id,),
            ).fetchall()
            invites = connection.execute(
                """
                SELECT id, token_prefix, role, expires_at, accepted_at, revoked_at, created_at
                FROM auth_organization_invites
                WHERE organization_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 20
                """,
                (organization_id,),
            ).fetchall()
        return AuthOrganizationDetail(
            **_organization_from_row(organization).model_dump(),
            members=[_organization_member_from_row(row) for row in members],
            printers=[_organization_printer_from_row(row) for row in printers],
            invites=[_organization_invite_from_row(row, base_url) for row in invites],
        )

    def create_organization_invite(
        self,
        actor_user_id: int,
        organization_id: int,
        payload: OrganizationInviteCreateRequest,
        base_url: str,
    ) -> AuthOrganizationInvite:
        token = new_secret("ptr_org")
        expires_at = format_dt(utc_now() + timedelta(days=7))
        with connect_database(self.database_path) as connection:
            self._require_org_manager(connection, organization_id, actor_user_id, "gerar convite")
            if payload.role == "owner":
                raise PermissionError("convite não pode transferir owner")
            cursor = connection.execute(
                """
                INSERT INTO auth_organization_invites (
                    organization_id, created_by_user_id, token_hash, token_prefix, role, expires_at
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (organization_id, actor_user_id, hash_token(token), token[:18], payload.role, expires_at),
            )
            row = connection.execute(
                """
                SELECT id, token_prefix, role, expires_at, accepted_at, revoked_at, created_at
                FROM auth_organization_invites
                WHERE id = ?
                """,
                (int(cursor.lastrowid),),
            ).fetchone()
        invite = _organization_invite_from_row(row, base_url)
        return invite.model_copy(update={"invite_url": _organization_invite_url(base_url, token)})

    def revoke_organization_invite(self, actor_user_id: int, organization_id: int, invite_id: int) -> None:
        with connect_database(self.database_path) as connection:
            self._require_org_manager(connection, organization_id, actor_user_id, "cancelar convite")
            row = connection.execute(
                """
                SELECT id, accepted_at, revoked_at
                FROM auth_organization_invites
                WHERE id = ? AND organization_id = ?
                """,
                (invite_id, organization_id),
            ).fetchone()
            if row is None:
                raise ValueError("convite não encontrado")
            if row["accepted_at"] is not None:
                raise ValueError("convite já aceito")
            if row["revoked_at"] is not None:
                return
            connection.execute(
                """
                UPDATE auth_organization_invites
                SET revoked_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (invite_id,),
            )

    def accept_organization_invite(self, user_id: int, token: str) -> AuthOrganization:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM auth_organization_invites
                WHERE token_hash = ?
                """,
                (hash_token(token),),
            ).fetchone()
            if row is None or row["revoked_at"] is not None or row["accepted_at"] is not None:
                raise ValueError("convite inválido")
            if str(row["expires_at"]) <= format_dt(utc_now()):
                raise ValueError("convite expirado")
            if str(row["role"]) == "owner":
                raise ValueError("convite de owner inválido")
            connection.execute(
                """
                INSERT INTO auth_organization_members (organization_id, user_id, role)
                VALUES (?, ?, ?)
                ON CONFLICT(organization_id, user_id) DO UPDATE SET
                    role = excluded.role,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (row["organization_id"], user_id, row["role"]),
            )
            connection.execute(
                """
                UPDATE auth_organization_invites
                SET accepted_by_user_id = ?, accepted_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (user_id, row["id"]),
            )
            organization = connection.execute(
                """
                SELECT o.id, o.name, o.owner_user_id, m.role
                FROM auth_organizations o
                JOIN auth_organization_members m ON m.organization_id = o.id
                WHERE o.id = ? AND m.user_id = ?
                """,
                (row["organization_id"], user_id),
            ).fetchone()
        return _organization_from_row(organization)

    def remove_organization_member(self, actor_user_id: int, organization_id: int, target_user_id: int) -> None:
        with connect_database(self.database_path) as connection:
            self._require_org_manager(connection, organization_id, actor_user_id, "remover membro")
            role = self._member_role(connection, organization_id, target_user_id)
            if role is None:
                raise ValueError("membro não encontrado")
            if role == "owner":
                raise PermissionError("owner não pode ser removido")
            connection.execute(
                "DELETE FROM auth_organization_members WHERE organization_id = ? AND user_id = ?",
                (organization_id, target_user_id),
            )

    def link_organization_printer(self, actor_user_id: int, organization_id: int, printer_id: int) -> None:
        with connect_database(self.database_path) as connection:
            self._require_org_manager(connection, organization_id, actor_user_id, "vincular impressora")
            visible = self._printer_visible_to_user(connection, actor_user_id, printer_id)
            if not visible:
                raise ValueError("impressora não encontrada")
            connection.execute(
                """
                INSERT OR IGNORE INTO auth_organization_printers (organization_id, printer_id, linked_by_user_id)
                VALUES (?, ?, ?)
                """,
                (organization_id, printer_id, actor_user_id),
            )

    def unlink_organization_printer(self, actor_user_id: int, organization_id: int, printer_id: int) -> None:
        with connect_database(self.database_path) as connection:
            self._require_org_manager(connection, organization_id, actor_user_id, "remover impressora")
            connection.execute(
                "DELETE FROM auth_organization_printers WHERE organization_id = ? AND printer_id = ?",
                (organization_id, printer_id),
            )

    def list_user_organizations(self, user_id: int) -> list[AuthOrganization]:
        with connect_database(self.database_path) as connection:
            return self._list_user_organizations(connection, user_id)

    def user_has_organization(self, user_id: int, organization_id: int) -> bool:
        with connect_database(self.database_path) as connection:
            return self._member_role(connection, organization_id, user_id) is not None

    def create_step_up(self, user_id: int, purpose: str) -> tuple[str, str]:
        token = new_secret("ptr_step")
        expires_at = utc_now() + STEP_UP_TTL
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO auth_step_up_tokens (user_id, token_hash, purpose, expires_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, hash_token(token), purpose, format_dt(expires_at)),
            )
        return token, format_dt(expires_at)

    def consume_step_up(self, user_id: int, token: str, purpose: str) -> bool:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                UPDATE auth_step_up_tokens
                SET consumed_at = CURRENT_TIMESTAMP
                WHERE id = (
                    SELECT id
                    FROM auth_step_up_tokens
                    WHERE user_id = ?
                      AND token_hash = ?
                      AND purpose = ?
                      AND consumed_at IS NULL
                      AND expires_at > CURRENT_TIMESTAMP
                    ORDER BY id
                    LIMIT 1
                )
                  AND consumed_at IS NULL
                RETURNING id
                """,
                (user_id, hash_token(token), purpose),
            ).fetchone()
        return row is not None

    def create_agent_credential(
        self,
        user_id: int,
        payload: AgentCredentialCreateRequest,
    ) -> AgentCredentialResponse:
        if payload.organization_id is not None and not self.user_has_organization(user_id, payload.organization_id):
            raise PermissionError("organização não pertence ao usuário")
        credential = new_secret("ptr_agent")
        credential_prefix = credential[:18]
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO agent_credentials (
                    organization_id, owner_user_id, label, credential_hash, credential_prefix
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (payload.organization_id, user_id, payload.label, hash_token(credential), credential_prefix),
            )
            row = connection.execute(
                """
                SELECT id, label, credential_prefix, organization_id, created_at
                FROM agent_credentials
                WHERE id = ?
                """,
                (int(cursor.lastrowid),),
            ).fetchone()
        return AgentCredentialResponse(
            id=int(row["id"]),
            label=str(row["label"]),
            credential=credential,
            credential_prefix=str(row["credential_prefix"]),
            organization_id=row["organization_id"],
            created_at=str(row["created_at"]),
        )

    def list_agent_credentials(self, user_id: int) -> list[AgentCredentialRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, label, credential_prefix, organization_id, revoked_at, created_at, last_used_at
                FROM agent_credentials
                WHERE owner_user_id = ?
                ORDER BY created_at DESC, id DESC
                """,
                (user_id,),
            ).fetchall()
        return [
            AgentCredentialRecord(
                id=int(row["id"]),
                label=str(row["label"]),
                credential_prefix=str(row["credential_prefix"]),
                organization_id=row["organization_id"],
                revoked=row["revoked_at"] is not None,
                created_at=str(row["created_at"]),
                last_used_at=row["last_used_at"],
            )
            for row in rows
        ]

    def verify_agent_credential(self, credential: str) -> AgentCredentialRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, label, credential_prefix, organization_id, revoked_at, created_at, last_used_at
                FROM agent_credentials
                WHERE credential_hash = ? AND revoked_at IS NULL
                """,
                (hash_token(credential),),
            ).fetchone()
            if row is None:
                return None
            connection.execute(
                "UPDATE agent_credentials SET last_used_at = CURRENT_TIMESTAMP WHERE id = ?",
                (int(row["id"]),),
            )
        return AgentCredentialRecord(
            id=int(row["id"]),
            label=str(row["label"]),
            credential_prefix=str(row["credential_prefix"]),
            organization_id=row["organization_id"],
            revoked=False,
            created_at=str(row["created_at"]),
            last_used_at=row["last_used_at"],
        )

    def _list_user_organizations(self, connection, user_id: int) -> list[AuthOrganization]:
        rows = connection.execute(
            """
            SELECT o.id, o.name, o.owner_user_id, m.role
            FROM auth_organization_members m
            JOIN auth_organizations o ON o.id = m.organization_id
            WHERE m.user_id = ?
            ORDER BY o.name ASC
            """,
            (user_id,),
        ).fetchall()
        return [_organization_from_row(row) for row in rows]

    def _member_role(self, connection, organization_id: int, user_id: int) -> str | None:
        row = connection.execute(
            """
            SELECT role
            FROM auth_organization_members
            WHERE organization_id = ? AND user_id = ?
            """,
            (organization_id, user_id),
        ).fetchone()
        return str(row["role"]) if row else None

    def _require_org_manager(self, connection, organization_id: int, user_id: int, action: str) -> None:
        role = self._member_role(connection, organization_id, user_id)
        if role not in ("owner", "admin"):
            raise PermissionError(f"usuário sem permissão para {action}")

    def _require_org_owner(self, connection, organization_id: int, user_id: int, action: str) -> None:
        role = self._member_role(connection, organization_id, user_id)
        if role != "owner":
            raise PermissionError(f"somente owner pode {action}")

    def _printer_visible_to_user(self, connection, user_id: int, printer_id: int) -> bool:
        row = connection.execute(
            """
            SELECT 1
            FROM printers p
            WHERE p.id = ?
              AND (
                p.owner_user_id = ?
                OR p.organization_id IN (
                    SELECT organization_id FROM auth_organization_members WHERE user_id = ?
                )
                OR EXISTS (
                    SELECT 1
                    FROM auth_organization_printers op
                    JOIN auth_organization_members m ON m.organization_id = op.organization_id
                    WHERE op.printer_id = p.id AND m.user_id = ?
                )
              )
            """,
            (printer_id, user_id, user_id, user_id),
        ).fetchone()
        return row is not None














def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_secret(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"






def protect_secret(database_path: Path, value: str) -> str:
    key = _load_or_create_auth_key(database_path)
    nonce = os.urandom(16)
    value_bytes = value.encode()
    stream = _keystream(key, nonce, len(value_bytes))
    payload = bytes(item ^ stream[index] for index, item in enumerate(value_bytes))
    signature = hmac.new(key, nonce + payload, hashlib.sha256).digest()
    return "v1:" + ":".join(
        base64.urlsafe_b64encode(part).decode()
        for part in [nonce, payload, signature]
    )


def unprotect_secret(database_path: Path, protected_value: str) -> str:
    if not protected_value.startswith("v1:"):
        raise ValueError("formato de segredo não suportado")
    encoded_parts = protected_value.removeprefix("v1:").split(":")
    if len(encoded_parts) != 3:
        raise ValueError("segredo inválido")
    nonce, payload, signature = [base64.urlsafe_b64decode(part.encode()) for part in encoded_parts]
    key = _load_or_create_auth_key(database_path)
    expected = hmac.new(key, nonce + payload, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("assinatura de segredo inválida")
    stream = _keystream(key, nonce, len(payload))
    return bytes(item ^ stream[index] for index, item in enumerate(payload)).decode()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_dt(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S")


def _user_from_row(row, organizations: list[AuthOrganization]) -> AuthUser:
    return AuthUser(
        id=int(row["id"]),
        email=str(row["email"]),
        display_name=row["display_name"],
        whatsapp=row["whatsapp"],
        telegram=row["telegram"],
        social_links=json.loads(row["social_links_json"] or "{}"),
        timezone=str(row["timezone"] or "America/Sao_Paulo"),
        mfa_enabled=bool(row["mfa_enabled"]),
        is_active=bool(row["is_active"]),
        platform_admin=is_platform_admin(str(row["email"])),
        created_at=str(row["created_at"]),
        organizations=organizations,
    )


def _organization_from_row(row) -> AuthOrganization:
    return AuthOrganization(
        id=int(row["id"]),
        name=str(row["name"]),
        owner_user_id=int(row["owner_user_id"]),
        role=row["role"],
    )


def _organization_member_from_row(row) -> AuthOrganizationMember:
    return AuthOrganizationMember(
        user_id=int(row["user_id"]),
        email=str(row["email"]),
        display_name=row["display_name"],
        role=row["role"],
        created_at=str(row["created_at"]),
    )


def _organization_printer_from_row(row) -> AuthOrganizationPrinter:
    return AuthOrganizationPrinter(
        printer_id=int(row["printer_id"]),
        name=str(row["name"]),
        moonraker_url=str(row["moonraker_url"]),
        linked_at=str(row["linked_at"]),
    )


def _organization_invite_from_row(row, base_url: str) -> AuthOrganizationInvite:
    return AuthOrganizationInvite(
        id=int(row["id"]),
        token_prefix=str(row["token_prefix"]),
        role=row["role"],
        invite_url="",
        expires_at=str(row["expires_at"]),
        accepted_at=row["accepted_at"],
        revoked_at=row["revoked_at"],
        created_at=str(row["created_at"]),
    )


def _organization_invite_url(base_url: str, token: str) -> str:
    return f"{base_url.rstrip('/')}/?section=account&org_invite={token}"




def _load_or_create_auth_key(database_path: Path) -> bytes:
    key_path = database_path.parent / "auth_secrets.key"
    if key_path.exists():
        return base64.urlsafe_b64decode(key_path.read_text().strip().encode())
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key = os.urandom(32)
    key_path.write_text(base64.urlsafe_b64encode(key).decode())
    try:
        key_path.chmod(0o600)
    except OSError:
        pass
    return key


def _keystream(key: bytes, nonce: bytes, length: int) -> bytes:
    output = b""
    counter = 0
    while len(output) < length:
        output += hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest()
        counter += 1
    return output[:length]
