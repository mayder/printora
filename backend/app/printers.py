from dataclasses import dataclass
import base64
import hashlib
import hmac
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.database import connect_database


HostAuditMode = Literal["disabled", "local", "ssh"]


class PrinterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    moonraker_url: HttpUrl
    host_audit_mode: HostAuditMode = "local"
    host_audit_ssh_target: str | None = Field(default=None, max_length=160)
    ssh_host: str | None = Field(default=None, max_length=160)
    ssh_port: int = Field(default=22, ge=1, le=65535)
    ssh_username: str | None = Field(default=None, max_length=80)
    ssh_credential: str | None = Field(default=None, max_length=500)
    location: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=500)


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
    location: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


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
    location: str | None
    notes: str | None
    is_active: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class PrinterRepository:
    database_path: Path

    def list_printers(self) -> list[PrinterRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT p.id, p.name, p.moonraker_url, p.host_audit_mode, p.host_audit_ssh_target,
                       p.location, p.notes, p.is_active, p.created_at, p.updated_at,
                       s.ssh_host, s.ssh_port, s.ssh_username, s.credential_configured
                FROM printers p
                LEFT JOIN printer_ssh_access s ON s.printer_id = p.id
                ORDER BY p.is_active DESC, p.name ASC
                """
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def get_printer(self, printer_id: int) -> PrinterRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT p.id, p.name, p.moonraker_url, p.host_audit_mode, p.host_audit_ssh_target,
                       p.location, p.notes, p.is_active, p.created_at, p.updated_at,
                       s.ssh_host, s.ssh_port, s.ssh_username, s.credential_configured
                FROM printers p
                LEFT JOIN printer_ssh_access s ON s.printer_id = p.id
                WHERE p.id = ?
                """,
                (printer_id,),
            ).fetchone()
        return _record_from_row(row) if row else None

    def create_printer(self, payload: PrinterCreate) -> PrinterRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO printers (
                    name, moonraker_url, host_audit_mode, host_audit_ssh_target, location, notes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.name.strip(),
                    str(payload.moonraker_url).rstrip("/"),
                    payload.host_audit_mode,
                    payload.host_audit_ssh_target,
                    payload.location,
                    payload.notes,
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
        location=row["location"],
        notes=row["notes"],
        is_active=bool(row["is_active"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )


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
