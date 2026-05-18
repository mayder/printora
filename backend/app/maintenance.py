from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.database import connect_database


MaintenanceEventType = Literal["maintenance", "failure", "adjustment", "note"]
TaskDueStatus = Literal["due", "ok", "unknown"]


class MaintenanceEventCreate(BaseModel):
    event_type: MaintenanceEventType = "maintenance"
    component: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=1, max_length=120)
    notes: str = Field(default="", max_length=1000)
    performed_at: str | None = Field(default=None, max_length=40)


class MaintenanceEventRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    performed_at: str
    event_type: MaintenanceEventType
    component: str | None
    title: str
    notes: str
    created_at: str


class MaintenanceTaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    component: str = Field(min_length=1, max_length=80)
    interval_days: int = Field(default=30, ge=1, le=3650)
    last_done_at: str | None = Field(default=None, max_length=40)


class MaintenanceTaskComplete(BaseModel):
    notes: str = Field(default="", max_length=1000)
    performed_at: str | None = Field(default=None, max_length=40)


class MaintenanceTaskRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    name: str
    component: str
    interval_days: int
    last_done_at: str | None
    is_active: bool
    created_at: str
    updated_at: str
    due_status: TaskDueStatus
    days_until_due: int | None


@dataclass(frozen=True)
class MaintenanceRepository:
    database_path: Path

    def create_event(self, printer_id: int, payload: MaintenanceEventCreate) -> MaintenanceEventRecord:
        performed_at = _clean_timestamp(payload.performed_at)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO maintenance_events (printer_id, performed_at, event_type, component, title, notes)
                VALUES (?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    performed_at,
                    payload.event_type,
                    _clean_optional(payload.component),
                    payload.title.strip(),
                    payload.notes.strip(),
                ),
            )
            event_id = int(cursor.lastrowid)
        event = self.get_event(event_id)
        if event is None:
            raise RuntimeError("maintenance event was not persisted")
        return event

    def list_events(self, printer_id: int, limit: int = 50) -> list[MaintenanceEventRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, performed_at, event_type, component, title, notes, created_at
                FROM maintenance_events
                WHERE printer_id = ?
                ORDER BY performed_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, limit),
            ).fetchall()
        return [_event_from_row(row) for row in rows]

    def get_event(self, event_id: int) -> MaintenanceEventRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, performed_at, event_type, component, title, notes, created_at
                FROM maintenance_events
                WHERE id = ?
                """,
                (event_id,),
            ).fetchone()
        return _event_from_row(row) if row else None

    def create_task(self, printer_id: int, payload: MaintenanceTaskCreate) -> MaintenanceTaskRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO maintenance_tasks (printer_id, name, component, interval_days, last_done_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    payload.name.strip(),
                    payload.component.strip(),
                    payload.interval_days,
                    _clean_timestamp(payload.last_done_at),
                ),
            )
            task_id = int(cursor.lastrowid)
        task = self.get_task(task_id)
        if task is None:
            raise RuntimeError("maintenance task was not persisted")
        return task

    def list_tasks(self, printer_id: int) -> list[MaintenanceTaskRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, name, component, interval_days, last_done_at,
                       is_active, created_at, updated_at
                FROM maintenance_tasks
                WHERE printer_id = ?
                ORDER BY is_active DESC, component ASC, name ASC
                """,
                (printer_id,),
            ).fetchall()
        return [_task_from_row(row) for row in rows]

    def get_task(self, task_id: int) -> MaintenanceTaskRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, name, component, interval_days, last_done_at,
                       is_active, created_at, updated_at
                FROM maintenance_tasks
                WHERE id = ?
                """,
                (task_id,),
            ).fetchone()
        return _task_from_row(row) if row else None

    def complete_task(self, task_id: int, payload: MaintenanceTaskComplete) -> MaintenanceEventRecord | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        performed_at = _clean_timestamp(payload.performed_at) or _now_text()
        event = self.create_event(
            task.printer_id,
            MaintenanceEventCreate(
                event_type="maintenance",
                component=task.component,
                title=task.name,
                notes=payload.notes,
                performed_at=performed_at,
            ),
        )
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE maintenance_tasks
                SET last_done_at = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (performed_at, task.id),
            )
        return event


def _event_from_row(row) -> MaintenanceEventRecord:
    return MaintenanceEventRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        performed_at=str(row["performed_at"]),
        event_type=row["event_type"],
        component=row["component"],
        title=str(row["title"]),
        notes=str(row["notes"]),
        created_at=str(row["created_at"]),
    )


def _task_from_row(row) -> MaintenanceTaskRecord:
    due_status, days_until_due = _calculate_due_status(row["last_done_at"], int(row["interval_days"]))
    return MaintenanceTaskRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        name=str(row["name"]),
        component=str(row["component"]),
        interval_days=int(row["interval_days"]),
        last_done_at=row["last_done_at"],
        is_active=bool(row["is_active"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        due_status=due_status,
        days_until_due=days_until_due,
    )


def _calculate_due_status(last_done_at: str | None, interval_days: int) -> tuple[TaskDueStatus, int | None]:
    if not last_done_at:
        return "due", 0
    parsed = _parse_datetime(last_done_at)
    if parsed is None:
        return "unknown", None
    elapsed_days = (datetime.now(timezone.utc) - parsed).days
    days_until_due = interval_days - elapsed_days
    if days_until_due <= 0:
        return "due", 0
    return "ok", days_until_due


def _parse_datetime(value: str) -> datetime | None:
    for candidate in (value, value.replace(" ", "T")):
        try:
            parsed = datetime.fromisoformat(candidate)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    return None


def _clean_timestamp(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None


def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None


def _now_text() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
