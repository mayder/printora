from dataclasses import dataclass
import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator

from app.database import connect_database


HostAuditMode = Literal["disabled", "local", "ssh"]
CloudPrinterStatus = Literal["sem_agente", "aguardando_pareamento", "online", "offline", "degradado", "revogado"]
AGENT_ONLINE_WINDOW_SECONDS = 120


class PrinterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    moonraker_url: HttpUrl
    host_audit_mode: HostAuditMode = "local"
    host_audit_ssh_target: str | None = Field(default=None, max_length=160)
    ssh_host: str | None = Field(default=None, max_length=160)
    ssh_port: int = Field(default=22, ge=1, le=65535)
    ssh_username: str | None = Field(default=None, max_length=80)
    ssh_credential: str | None = Field(default=None, max_length=500)
    cloud_model: str | None = Field(default=None, max_length=120)
    cloud_tags: list[str] = Field(default_factory=list, max_length=12)
    location: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=500)
    organization_id: int | None = Field(default=None, ge=1)

    @field_validator("cloud_tags")
    @classmethod
    def clean_cloud_tags(cls, value: list[str]) -> list[str]:
        return _clean_tags(value)


class PrinterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    moonraker_url: HttpUrl | None = None
    host_audit_mode: HostAuditMode | None = None
    host_audit_ssh_target: str | None = Field(default=None, max_length=160)
    ssh_host: str | None = Field(default=None, max_length=160)
    ssh_port: int | None = Field(default=None, ge=1, le=65535)
    ssh_username: str | None = Field(default=None, max_length=80)
    ssh_credential: str | None = Field(default=None, max_length=500)
    clear_ssh_credential: bool = False
    cloud_model: str | None = Field(default=None, max_length=120)
    cloud_tags: list[str] | None = Field(default=None, max_length=12)
    location: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=500)
    organization_id: int | None = Field(default=None, ge=1)
    is_active: bool | None = None

    @field_validator("cloud_tags")
    @classmethod
    def clean_cloud_tags(cls, value: list[str] | None) -> list[str] | None:
        return _clean_tags(value) if value is not None else None


class PrinterRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    moonraker_url: str
    host_audit_mode: HostAuditMode
    host_audit_ssh_target: str | None
    ssh_host: str | None = None
    ssh_port: int | None = None
    ssh_username: str | None = None
    ssh_credential_configured: bool = False
    cloud_model: str | None = None
    cloud_tags: list[str] = Field(default_factory=list)
    cloud_status: CloudPrinterStatus = "sem_agente"
    active_agent_count: int = 0
    latest_agent_version: str | None = None
    latest_agent_last_seen_at: str | None = None
    latest_snapshot_at: str | None = None
    location: str | None
    notes: str | None
    owner_user_id: int | None = None
    organization_id: int | None = None
    public_profile_enabled: bool = False
    catalog_variant_id: int | None = None
    public_name: str | None = None
    public_description: str | None = None
    public_mods: list[str] = Field(default_factory=list)
    public_images: list[str] = Field(default_factory=list)
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class PrinterSshAccess:
    host: str
    port: int
    username: str
    credential: str | None


@dataclass(frozen=True)
class PrinterRepository:
    database_path: Path
    user_id: int | None = None
    organization_ids: tuple[int, ...] = ()

    def list_printers(self) -> list[PrinterRecord]:
        with connect_database(self.database_path) as connection:
            where_clause, params = self._visibility_where("p")
            rows = connection.execute(
                f"""
                SELECT p.id, p.name, p.moonraker_url, p.host_audit_mode, p.host_audit_ssh_target,
                       p.location, p.notes, p.cloud_model, p.cloud_tags_json,
                       p.public_profile_enabled, p.catalog_variant_id, p.public_name,
                       p.public_description, p.public_mods_json, p.public_images_json,
                       p.owner_user_id, p.organization_id, p.is_active, p.created_at, p.updated_at,
                       (
                         SELECT COUNT(*)
                         FROM printer_agents a
                         WHERE a.printer_id = p.id AND a.status = 'active' AND a.revoked_at IS NULL
                       ) AS active_agent_count,
                       (
                         SELECT COUNT(*)
                         FROM printer_agents a
                         WHERE a.printer_id = p.id AND a.status = 'revoked'
                       ) AS revoked_agent_count,
                       (
                         SELECT COUNT(*)
                         FROM printer_pairing_tokens t
                         WHERE t.printer_id = p.id
                           AND t.consumed_at IS NULL
                           AND t.revoked_at IS NULL
                           AND t.expires_at > CURRENT_TIMESTAMP
                       ) AS active_pairing_token_count,
                       (
                         SELECT a.agent_version
                         FROM printer_agents a
                         WHERE a.printer_id = p.id AND a.status = 'active' AND a.revoked_at IS NULL
                         ORDER BY a.last_seen_at IS NULL, a.last_seen_at DESC, a.paired_at DESC, a.id DESC
                         LIMIT 1
                       ) AS latest_agent_version,
                       (
                         SELECT a.last_seen_at
                         FROM printer_agents a
                         WHERE a.printer_id = p.id AND a.status = 'active' AND a.revoked_at IS NULL
                         ORDER BY a.last_seen_at IS NULL, a.last_seen_at DESC, a.paired_at DESC, a.id DESC
                         LIMIT 1
                       ) AS latest_agent_last_seen_at,
                       (
                         SELECT s.created_at
                         FROM printer_snapshots s
                         WHERE s.printer_id = p.id
                         ORDER BY s.created_at DESC, s.id DESC
                         LIMIT 1
                       ) AS latest_snapshot_at,
                       s.ssh_host, s.ssh_port, s.ssh_username, s.credential_configured
                FROM printers p
                LEFT JOIN printer_ssh_access s ON s.printer_id = p.id
                {where_clause}
                ORDER BY p.is_active DESC, p.name ASC
                """,
                params,
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def get_printer(self, printer_id: int) -> PrinterRecord | None:
        with connect_database(self.database_path) as connection:
            where_clause, visibility_params = self._visibility_where("p")
            visibility_sql = where_clause.replace("WHERE", "AND", 1) if where_clause else ""
            row = connection.execute(
                f"""
                SELECT p.id, p.name, p.moonraker_url, p.host_audit_mode, p.host_audit_ssh_target,
                       p.location, p.notes, p.cloud_model, p.cloud_tags_json,
                       p.public_profile_enabled, p.catalog_variant_id, p.public_name,
                       p.public_description, p.public_mods_json, p.public_images_json,
                       p.owner_user_id, p.organization_id, p.is_active, p.created_at, p.updated_at,
                       (
                         SELECT COUNT(*)
                         FROM printer_agents a
                         WHERE a.printer_id = p.id AND a.status = 'active' AND a.revoked_at IS NULL
                       ) AS active_agent_count,
                       (
                         SELECT COUNT(*)
                         FROM printer_agents a
                         WHERE a.printer_id = p.id AND a.status = 'revoked'
                       ) AS revoked_agent_count,
                       (
                         SELECT COUNT(*)
                         FROM printer_pairing_tokens t
                         WHERE t.printer_id = p.id
                           AND t.consumed_at IS NULL
                           AND t.revoked_at IS NULL
                           AND t.expires_at > CURRENT_TIMESTAMP
                       ) AS active_pairing_token_count,
                       (
                         SELECT a.agent_version
                         FROM printer_agents a
                         WHERE a.printer_id = p.id AND a.status = 'active' AND a.revoked_at IS NULL
                         ORDER BY a.last_seen_at IS NULL, a.last_seen_at DESC, a.paired_at DESC, a.id DESC
                         LIMIT 1
                       ) AS latest_agent_version,
                       (
                         SELECT a.last_seen_at
                         FROM printer_agents a
                         WHERE a.printer_id = p.id AND a.status = 'active' AND a.revoked_at IS NULL
                         ORDER BY a.last_seen_at IS NULL, a.last_seen_at DESC, a.paired_at DESC, a.id DESC
                         LIMIT 1
                       ) AS latest_agent_last_seen_at,
                       (
                         SELECT s.created_at
                         FROM printer_snapshots s
                         WHERE s.printer_id = p.id
                         ORDER BY s.created_at DESC, s.id DESC
                         LIMIT 1
                       ) AS latest_snapshot_at,
                       s.ssh_host, s.ssh_port, s.ssh_username, s.credential_configured
                FROM printers p
                LEFT JOIN printer_ssh_access s ON s.printer_id = p.id
                WHERE p.id = ?
                {visibility_sql}
                """,
                (printer_id, *visibility_params),
            ).fetchone()
        return _record_from_row(row) if row else None

    def get_ssh_access(self, printer_id: int) -> PrinterSshAccess | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT ssh_host, ssh_port, ssh_username, credential_blob, credential_configured
                FROM printer_ssh_access
                WHERE printer_id = ?
                """,
                (printer_id,),
            ).fetchone()
        if row is None or not row["ssh_host"] or not row["ssh_username"]:
            return None
        credential = None
        if row["credential_blob"]:
            try:
                credential = _unprotect_credential(self.database_path, str(row["credential_blob"]))
            except ValueError:
                credential = None
        return PrinterSshAccess(
            host=str(row["ssh_host"]),
            port=int(row["ssh_port"] or 22),
            username=str(row["ssh_username"]),
            credential=credential,
        )

    def create_printer(self, payload: PrinterCreate) -> PrinterRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO printers (
                    name, moonraker_url, host_audit_mode, host_audit_ssh_target,
                    location, notes, cloud_model, cloud_tags_json, owner_user_id, organization_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.name.strip(),
                    str(payload.moonraker_url).rstrip("/"),
                    payload.host_audit_mode,
                    payload.host_audit_ssh_target,
                    payload.location,
                    payload.notes,
                    _clean_optional_text(payload.cloud_model),
                    _tags_json(payload.cloud_tags),
                    self.user_id,
                    self._allowed_organization_id(payload.organization_id),
                ),
            )
            printer_id = int(cursor.lastrowid)
            self._upsert_ssh_access(connection, printer_id, payload)
        record = self.get_printer(printer_id)
        if record is None:
            raise RuntimeError("printer was not persisted")
        return record

    def update_printer(self, printer_id: int, payload: PrinterUpdate) -> PrinterRecord | None:
        current = self.get_printer(printer_id)
        if current is None:
            return None

        values = payload.model_dump(exclude_unset=True)
        ssh_values = {
            key: values.pop(key)
            for key in [
                "ssh_host",
                "ssh_port",
                "ssh_username",
                "ssh_credential",
                "clear_ssh_credential",
            ]
            if key in values
        }
        if "moonraker_url" in values and values["moonraker_url"] is not None:
            values["moonraker_url"] = str(values["moonraker_url"]).rstrip("/")
        if "name" in values and values["name"] is not None:
            values["name"] = values["name"].strip()
        if "is_active" in values and values["is_active"] is not None:
            values["is_active"] = 1 if values["is_active"] else 0
        if "host_audit_ssh_target" in values and values["host_audit_ssh_target"] is not None:
            values["host_audit_ssh_target"] = values["host_audit_ssh_target"].strip() or None
        if "cloud_model" in values:
            values["cloud_model"] = _clean_optional_text(values["cloud_model"])
        if "cloud_tags" in values:
            values["cloud_tags_json"] = _tags_json(values.pop("cloud_tags") or [])
        if "organization_id" in values:
            values["organization_id"] = self._allowed_organization_id(values["organization_id"])

        if values or ssh_values:
            with connect_database(self.database_path) as connection:
                if values:
                    assignments = ", ".join(f"{key} = ?" for key in values)
                    params = [*values.values(), printer_id]
                    connection.execute(
                        f"UPDATE printers SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        params,
                    )
                if ssh_values:
                    self._upsert_ssh_access(connection, printer_id, ssh_values)
                    ssh_target = _build_ssh_target(
                        ssh_values.get("ssh_username", current.ssh_username),
                        ssh_values.get("ssh_host", current.ssh_host),
                        ssh_values.get("ssh_port", current.ssh_port),
                    )
                    if ssh_target:
                        connection.execute(
                            """
                            UPDATE printers
                            SET host_audit_mode = 'ssh',
                                host_audit_ssh_target = ?,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                            """,
                            (ssh_target, printer_id),
                        )
        return self.get_printer(printer_id)

    def _visibility_where(self, table_alias: str) -> tuple[str, tuple[object, ...]]:
        if self.user_id is None:
            return "", ()
        params: list[object] = [self.user_id]
        clauses = [f"{table_alias}.owner_user_id = ?"]
        if self.organization_ids:
            placeholders = ", ".join("?" for _ in self.organization_ids)
            clauses.append(f"{table_alias}.organization_id IN ({placeholders})")
            params.extend(self.organization_ids)
            clauses.append(
                f"""
                EXISTS (
                    SELECT 1 FROM auth_organization_printers op
                    WHERE op.printer_id = {table_alias}.id
                      AND op.organization_id IN ({placeholders})
                )
                """
            )
            params.extend(self.organization_ids)
        return "WHERE (" + " OR ".join(clauses) + ")", tuple(params)

    def _allowed_organization_id(self, organization_id: int | None) -> int | None:
        if organization_id is None:
            return None
        if self.user_id is None or organization_id in self.organization_ids:
            return organization_id
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT 1
                FROM auth_organization_members
                WHERE organization_id = ? AND user_id = ?
                """,
                (organization_id, self.user_id),
            ).fetchone()
        if row is not None:
            return organization_id
        raise ValueError("organização não pertence ao usuário")

    def _upsert_ssh_access(self, connection, printer_id: int, payload: PrinterCreate | dict[str, object]) -> None:
        values = payload.model_dump(exclude_unset=True) if isinstance(payload, BaseModel) else payload
        ssh_keys = {"ssh_host", "ssh_port", "ssh_username", "ssh_credential", "clear_ssh_credential"}
        if not any(key in values for key in ssh_keys):
            return

        current = connection.execute(
            """
            SELECT ssh_host, ssh_port, ssh_username, credential_blob, credential_configured
            FROM printer_ssh_access
            WHERE printer_id = ?
            """,
            (printer_id,),
        ).fetchone()
        ssh_host = _clean_optional_text(values.get("ssh_host", current["ssh_host"] if current else None))
        ssh_port = int(values.get("ssh_port", current["ssh_port"] if current else 22) or 22)
        ssh_username = _clean_optional_text(values.get("ssh_username", current["ssh_username"] if current else None))
        credential_blob = current["credential_blob"] if current else None
        credential_configured = bool(current["credential_configured"]) if current else False

        if values.get("clear_ssh_credential"):
            credential_blob = None
            credential_configured = False
        if "ssh_credential" in values and values["ssh_credential"] not in (None, ""):
            credential_blob = _protect_credential(self.database_path, str(values["ssh_credential"]))
            credential_configured = True

        connection.execute(
            """
            INSERT INTO printer_ssh_access (
                printer_id, ssh_host, ssh_port, ssh_username, credential_blob, credential_configured
            )
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(printer_id) DO UPDATE SET
                ssh_host = excluded.ssh_host,
                ssh_port = excluded.ssh_port,
                ssh_username = excluded.ssh_username,
                credential_blob = excluded.credential_blob,
                credential_configured = excluded.credential_configured,
                updated_at = CURRENT_TIMESTAMP
            """,
            (printer_id, ssh_host, ssh_port, ssh_username, credential_blob, 1 if credential_configured else 0),
        )

        ssh_target = _build_ssh_target(ssh_username, ssh_host, ssh_port)
        if ssh_target:
            connection.execute(
                """
                UPDATE printers
                SET host_audit_mode = 'ssh',
                    host_audit_ssh_target = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (ssh_target, printer_id),
            )


def _record_from_row(row) -> PrinterRecord:
    active_agent_count = int(row["active_agent_count"] or 0)
    revoked_agent_count = int(row["revoked_agent_count"] or 0)
    active_pairing_token_count = int(row["active_pairing_token_count"] or 0)
    latest_agent_last_seen_at = row["latest_agent_last_seen_at"]
    return PrinterRecord(
        id=int(row["id"]),
        name=str(row["name"]),
        moonraker_url=str(row["moonraker_url"]),
        host_audit_mode=row["host_audit_mode"],
        host_audit_ssh_target=row["host_audit_ssh_target"],
        ssh_host=row["ssh_host"],
        ssh_port=int(row["ssh_port"]) if row["ssh_port"] is not None else None,
        ssh_username=row["ssh_username"],
        ssh_credential_configured=bool(row["credential_configured"]),
        cloud_model=row["cloud_model"],
        cloud_tags=_parse_tags(row["cloud_tags_json"]),
        cloud_status=_cloud_status(
            active_agent_count=active_agent_count,
            revoked_agent_count=revoked_agent_count,
            active_pairing_token_count=active_pairing_token_count,
            latest_agent_last_seen_at=latest_agent_last_seen_at,
        ),
        active_agent_count=active_agent_count,
        latest_agent_version=row["latest_agent_version"],
        latest_agent_last_seen_at=latest_agent_last_seen_at,
        latest_snapshot_at=row["latest_snapshot_at"],
        location=row["location"],
        notes=row["notes"],
        owner_user_id=row["owner_user_id"],
        organization_id=row["organization_id"],
        public_profile_enabled=bool(row["public_profile_enabled"]),
        catalog_variant_id=row["catalog_variant_id"],
        public_name=row["public_name"],
        public_description=row["public_description"],
        public_mods=_parse_text_list(row["public_mods_json"], limit=20),
        public_images=_parse_public_images(row["public_images_json"]),
        is_active=bool(row["is_active"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


def _clean_tags(values: list[str]) -> list[str]:
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        tag = str(value).strip().lower()
        if not tag or tag in seen:
            continue
        cleaned.append(tag[:32])
        seen.add(tag)
        if len(cleaned) >= 12:
            break
    return cleaned


def _tags_json(values: list[str]) -> str:
    return json.dumps(_clean_tags(values), ensure_ascii=False)


def _parse_tags(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return _clean_tags([str(item) for item in parsed])


def _parse_public_images(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()][:6]


def _parse_text_list(value: str | None, *, limit: int) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [str(item) for item in parsed if str(item).strip()][:limit]


def _cloud_status(
    *,
    active_agent_count: int,
    revoked_agent_count: int,
    active_pairing_token_count: int,
    latest_agent_last_seen_at: str | None,
) -> CloudPrinterStatus:
    if active_agent_count <= 0:
        if active_pairing_token_count > 0:
            return "aguardando_pareamento"
        if revoked_agent_count > 0:
            return "revogado"
        return "sem_agente"
    if latest_agent_last_seen_at is None:
        return "aguardando_pareamento"
    age_seconds = _age_seconds(latest_agent_last_seen_at)
    return "online" if age_seconds is not None and age_seconds <= AGENT_ONLINE_WINDOW_SECONDS else "offline"


def _age_seconds(value: str | None) -> int | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return max(0, int((datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).total_seconds()))


def _clean_optional_text(value: object) -> str | None:
    if value is None:
        return None
    cleaned = str(value).strip()
    return cleaned or None


def _build_ssh_target(username: str | None, host: str | None, port: int | None) -> str | None:
    if not username or not host:
        return None
    return f"{username}@{host}"


def _protect_credential(database_path: Path, value: str) -> str:
    key = _load_or_create_local_key(database_path)
    nonce = os.urandom(16)
    value_bytes = value.encode()
    stream = _keystream(key, nonce, len(value_bytes))
    payload = bytes(item ^ stream[index] for index, item in enumerate(value_bytes))
    signature = hmac.new(key, nonce + payload, hashlib.sha256).digest()
    return "v1:" + ":".join(
        base64.urlsafe_b64encode(part).decode()
        for part in [nonce, payload, signature]
    )


def _unprotect_credential(database_path: Path, protected_value: str) -> str:
    if not protected_value.startswith("v1:"):
        raise ValueError("unsupported credential format")
    encoded_parts = protected_value.removeprefix("v1:").split(":")
    if len(encoded_parts) != 3:
        raise ValueError("invalid credential payload")
    nonce, payload, signature = [base64.urlsafe_b64decode(part.encode()) for part in encoded_parts]
    key = _load_or_create_local_key(database_path)
    expected = hmac.new(key, nonce + payload, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("invalid credential signature")
    stream = _keystream(key, nonce, len(payload))
    value_bytes = bytes(item ^ stream[index] for index, item in enumerate(payload))
    return value_bytes.decode()


def _load_or_create_local_key(database_path: Path) -> bytes:
    key_path = database_path.parent / "printer_access.key"
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


def _keystream(key: bytes, nonce: bytes, size: int) -> bytes:
    chunks: list[bytes] = []
    counter = 0
    while sum(len(chunk) for chunk in chunks) < size:
        chunks.append(hmac.new(key, nonce + counter.to_bytes(4, "big"), hashlib.sha256).digest())
        counter += 1
    return b"".join(chunks)[:size]
