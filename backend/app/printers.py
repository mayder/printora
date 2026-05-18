from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.database import connect_database


HostAuditMode = Literal["disabled", "local", "ssh"]


class PrinterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    moonraker_url: HttpUrl
    host_audit_mode: HostAuditMode = "disabled"
    host_audit_ssh_target: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=120)
    notes: str | None = Field(default=None, max_length=500)


class PrinterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    moonraker_url: HttpUrl | None = None
    host_audit_mode: HostAuditMode | None = None
    host_audit_ssh_target: str | None = Field(default=None, max_length=160)
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
                SELECT id, name, moonraker_url, host_audit_mode, host_audit_ssh_target,
                       location, notes, is_active, created_at, updated_at
                FROM printers
                ORDER BY is_active DESC, name ASC
                """
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def get_printer(self, printer_id: int) -> PrinterRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, name, moonraker_url, host_audit_mode, host_audit_ssh_target,
                       location, notes, is_active, created_at, updated_at
                FROM printers
                WHERE id = ?
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
        record = self.get_printer(printer_id)
        if record is None:
            raise RuntimeError("printer was not persisted")
        return record

    def update_printer(self, printer_id: int, payload: PrinterUpdate) -> PrinterRecord | None:
        current = self.get_printer(printer_id)
        if current is None:
            return None

        values = payload.model_dump(exclude_unset=True)
        if "moonraker_url" in values and values["moonraker_url"] is not None:
            values["moonraker_url"] = str(values["moonraker_url"]).rstrip("/")
        if "name" in values and values["name"] is not None:
            values["name"] = values["name"].strip()
        if "is_active" in values and values["is_active"] is not None:
            values["is_active"] = 1 if values["is_active"] else 0

        if values:
            assignments = ", ".join(f"{key} = ?" for key in values)
            params = [*values.values(), printer_id]
            with connect_database(self.database_path) as connection:
                connection.execute(
                    f"UPDATE printers SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    params,
                )
        return self.get_printer(printer_id)


def _record_from_row(row) -> PrinterRecord:
    return PrinterRecord(
        id=int(row["id"]),
        name=str(row["name"]),
        moonraker_url=str(row["moonraker_url"]),
        host_audit_mode=row["host_audit_mode"],
        host_audit_ssh_target=row["host_audit_ssh_target"],
        location=row["location"],
        notes=row["notes"],
        is_active=bool(row["is_active"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )
