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
import struct
import time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.database import connect_database


OrganizationRole = Literal["owner", "admin", "operator"]

SESSION_TTL = timedelta(hours=12)
MFA_CHALLENGE_TTL = timedelta(minutes=5)
STEP_UP_TTL = timedelta(minutes=5)
PBKDF2_ITERATIONS = 210_000

CURRENT_AUTH_USER_ID: ContextVar[int | None] = ContextVar("current_auth_user_id", default=None)
CURRENT_AUTH_ORGANIZATION_IDS: ContextVar[tuple[int, ...]] = ContextVar("current_auth_organization_ids", default=())


class UserContactLinks(BaseModel):
    instagram: str | None = Field(default=None, max_length=160)
    x: str | None = Field(default=None, max_length=160)
    facebook: str | None = Field(default=None, max_length=160)
    website: str | None = Field(default=None, max_length=240)


class UserRegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=200)
    display_name: str | None = Field(default=None, max_length=120)
    whatsapp: str | None = Field(default=None, max_length=40)
    telegram: str | None = Field(default=None, max_length=80)
    social_links: UserContactLinks = Field(default_factory=UserContactLinks)

    @field_validator("display_name", "whatsapp", "telegram")
    @classmethod
    def clean_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return clean_email(value)


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=200)

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return clean_email(value)


class MfaLoginRequest(BaseModel):
    challenge_token: str = Field(min_length=20, max_length=240)
    code: str = Field(min_length=6, max_length=8)


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("nome da organização é obrigatório")
        return cleaned


class OrganizationMemberAddRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    role: OrganizationRole = "operator"

    @field_validator("email")
    @classmethod
    def clean_email(cls, value: str) -> str:
        return clean_email(value)


class MfaCodeRequest(BaseModel):
    code: str = Field(min_length=6, max_length=8)


class StepUpRequest(BaseModel):
    purpose: str = Field(default="destructive_action", min_length=3, max_length=80)
    password: str | None = Field(default=None, max_length=200)
    code: str | None = Field(default=None, min_length=6, max_length=8)


class AgentCredentialCreateRequest(BaseModel):
    label: str = Field(min_length=1, max_length=120)
    organization_id: int | None = Field(default=None, ge=1)

    @field_validator("label")
    @classmethod
    def clean_label(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("identificação do agente é obrigatória")
        return cleaned


class AuthOrganization(BaseModel):
    id: int
    name: str
    role: OrganizationRole
    owner_user_id: int


class AuthUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    display_name: str | None
    whatsapp: str | None
    telegram: str | None
    social_links: dict[str, str | None]
    mfa_enabled: bool
    is_active: bool
    created_at: str
    organizations: list[AuthOrganization] = Field(default_factory=list)


class AuthSessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    user: AuthUser


class LoginResponse(BaseModel):
    access_token: str | None = None
    token_type: str = "bearer"
    expires_at: str | None = None
    user: AuthUser | None = None
    mfa_required: bool = False
    challenge_token: str | None = None


class MfaSetupResponse(BaseModel):
    secret: str
    otpauth_uri: str


class StepUpResponse(BaseModel):
    step_up_token: str
    expires_at: str


class AgentCredentialResponse(BaseModel):
    id: int
    label: str
    credential: str
    credential_prefix: str
    organization_id: int | None
    created_at: str


class AgentCredentialRecord(BaseModel):
    id: int
    label: str
    credential_prefix: str
    organization_id: int | None
    revoked: bool
    created_at: str
    last_used_at: str | None


@dataclass(frozen=True)
class CurrentUser:
    user: AuthUser
    token: str


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
                        email, password_hash, display_name, whatsapp, telegram, social_links_json
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload.email.lower(),
                        hash_password(payload.password),
                        payload.display_name,
                        payload.whatsapp,
                        payload.telegram,
                        payload.social_links.model_dump_json(),
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
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE auth_users
                SET mfa_secret_protected = ?, mfa_enabled = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (protect_secret(self.database_path, secret), 1 if enabled else 0, user_id),
            )

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
                SELECT id
                FROM auth_step_up_tokens
                WHERE user_id = ?
                  AND token_hash = ?
                  AND purpose = ?
                  AND consumed_at IS NULL
                  AND expires_at > CURRENT_TIMESTAMP
                """,
                (user_id, hash_token(token), purpose),
            ).fetchone()
            if row is None:
                return False
            connection.execute(
                "UPDATE auth_step_up_tokens SET consumed_at = CURRENT_TIMESTAMP WHERE id = ?",
                (int(row["id"]),),
            )
        return True

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


def login(repository: AuthRepository, payload: LoginRequest) -> LoginResponse:
    user = repository.get_user_by_email(payload.email)
    if user is None or not user.is_active:
        raise ValueError("email ou senha inválidos")
    password_hash = repository.get_password_hash(user.id)
    if password_hash is None or not verify_password(payload.password, password_hash):
        raise ValueError("email ou senha inválidos")
    if user.mfa_enabled:
        return LoginResponse(mfa_required=True, challenge_token=repository.create_mfa_challenge(user.id))
    token, expires_at = repository.create_session(user.id)
    return LoginResponse(access_token=token, expires_at=expires_at, user=user)


def complete_mfa_login(repository: AuthRepository, payload: MfaLoginRequest) -> AuthSessionResponse:
    user = repository.consume_mfa_challenge(payload.challenge_token)
    if user is None:
        raise ValueError("desafio 2FA inválido ou expirado")
    secret = repository.get_mfa_secret(user.id)
    if secret is None or not verify_totp(secret, payload.code):
        raise ValueError("código 2FA inválido")
    token, expires_at = repository.create_session(user.id)
    return AuthSessionResponse(access_token=token, expires_at=expires_at, user=user)


def setup_mfa(user: AuthUser) -> MfaSetupResponse:
    secret = base64.b32encode(os.urandom(20)).decode().rstrip("=")
    issuer = "Printora"
    label = f"{issuer}:{user.email}"
    uri = f"otpauth://totp/{label}?secret={secret}&issuer={issuer}&digits=6&period=30"
    return MfaSetupResponse(secret=secret, otpauth_uri=uri)


def validate_step_up(repository: AuthRepository, user: AuthUser, payload: StepUpRequest) -> StepUpResponse:
    if user.mfa_enabled:
        secret = repository.get_mfa_secret(user.id)
        if secret is None or payload.code is None or not verify_totp(secret, payload.code):
            raise ValueError("código 2FA obrigatório para ação crítica")
    else:
        password_hash = repository.get_password_hash(user.id)
        if payload.password is None or password_hash is None or not verify_password(payload.password, password_hash):
            raise ValueError("senha obrigatória para ação crítica")
    token, expires_at = repository.create_step_up(user.id, payload.purpose)
    return StepUpResponse(step_up_token=token, expires_at=expires_at)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256:" + ":".join(
        [
            str(PBKDF2_ITERATIONS),
            base64.urlsafe_b64encode(salt).decode(),
            base64.urlsafe_b64encode(digest).decode(),
        ]
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations_text, salt_text, digest_text = password_hash.split(":", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode())
        expected = base64.urlsafe_b64decode(digest_text.encode())
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, int(iterations_text))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def new_secret(prefix: str) -> str:
    return f"{prefix}_{secrets.token_urlsafe(32)}"


def verify_totp(secret: str, code: str, now: int | None = None) -> bool:
    cleaned = "".join(character for character in code if character.isdigit())
    if len(cleaned) != 6:
        return False
    timestamp = int(time.time()) if now is None else now
    for offset in (-1, 0, 1):
        if hmac.compare_digest(totp_code(secret, timestamp + offset * 30), cleaned):
            return True
    return False


def clean_email(value: str) -> str:
    cleaned = value.strip().lower()
    if "@" not in cleaned or cleaned.startswith("@") or cleaned.endswith("@"):
        raise ValueError("email inválido")
    return cleaned


def totp_code(secret: str, timestamp: int | None = None) -> str:
    current = int(time.time()) if timestamp is None else timestamp
    counter = current // 30
    key = _base32_decode(secret)
    digest = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    value = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return f"{value % 1_000_000:06d}"


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
        mfa_enabled=bool(row["mfa_enabled"]),
        is_active=bool(row["is_active"]),
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


def _base32_decode(secret: str) -> bytes:
    normalized = secret.strip().replace(" ", "").upper()
    padding = "=" * ((8 - len(normalized) % 8) % 8)
    return base64.b32decode((normalized + padding).encode())


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
