from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.database import connect_database


MaintenanceEventType = Literal["maintenance", "failure", "adjustment", "note"]
MaintenanceIntervalKind = Literal["days", "print_hours"]
TaskDueStatus = Literal["due", "soon", "ok", "unknown", "not_validated", "needs_review"]


DEFAULT_PREVENTIVE_TASKS = [
    {"name": "Limpar superfície da mesa", "component": "mesa", "interval_days": 7},
    {"name": "Inspecionar adesão da mesa", "component": "mesa", "interval_days": 14},
    {"name": "Verificar nivelamento mecânico da mesa", "component": "mesa", "interval_days": 30},
    {"name": "Revisar Z-offset aprovado", "component": "calibração", "interval_days": 30},
    {"name": "Refazer malha da mesa", "component": "calibração", "interval_days": 30},
    {"name": "Limpar poeira da estrutura", "component": "estrutura", "interval_days": 30},
    {"name": "Conferir parafusos estruturais", "component": "estrutura", "interval_days": 60},
    {"name": "Conferir esquadro da estrutura", "component": "estrutura", "interval_days": 90},
    {"name": "Verificar tensão das correias", "component": "movimento", "interval_days": 30},
    {"name": "Inspecionar desgaste das correias", "component": "movimento", "interval_days": 60},
    {"name": "Lubrificar trilhos lineares", "component": "movimento", "interval_days": 45},
    {"name": "Limpar trilhos e guias", "component": "movimento", "interval_days": 30},
    {"name": "Inspecionar roldanas, polias e idlers", "component": "movimento", "interval_days": 60},
    {"name": "Conferir aperto de polias nos motores", "component": "movimento", "interval_days": 60},
    {"name": "Limpar bico externamente", "component": "hotend", "interval_days": 14},
    {"name": "Inspecionar bico por desgaste ou entupimento", "component": "hotend", "interval_days": 30},
    {"name": "Conferir aperto do hotend em temperatura segura", "component": "hotend", "interval_days": 90},
    {"name": "Inspecionar vazamento de filamento no hotend", "component": "hotend", "interval_days": 30},
    {"name": "Limpar engrenagens do extrusor", "component": "extrusor", "interval_days": 30},
    {"name": "Verificar pressão/tensão do extrusor", "component": "extrusor", "interval_days": 30},
    {"name": "Inspecionar tubo PTFE ou guia de filamento", "component": "filamento", "interval_days": 45},
    {"name": "Limpar caminho do filamento", "component": "filamento", "interval_days": 30},
    {"name": "Inspecionar sensor de filamento", "component": "filamento", "interval_days": 45},
    {"name": "Limpar fans e dutos", "component": "refrigeração", "interval_days": 30},
    {"name": "Verificar ruído ou folga dos fans", "component": "refrigeração", "interval_days": 30},
    {"name": "Limpar filtro de ar ou carvão ativado", "component": "refrigeração", "interval_days": 30},
    {"name": "Inspecionar cabos do toolhead", "component": "elétrica", "interval_days": 30},
    {"name": "Inspecionar conectores CAN/USB", "component": "elétrica", "interval_days": 30},
    {"name": "Conferir fixação e alívio de tensão dos cabos", "component": "elétrica", "interval_days": 45},
    {"name": "Inspecionar fonte, borne e aterramento visualmente", "component": "elétrica", "interval_days": 90},
    {"name": "Conferir câmera e iluminação", "component": "acessórios", "interval_days": 60},
    {"name": "Conferir spool holder e caminho até a impressora", "component": "acessórios", "interval_days": 30},
    {"name": "Revisar macros e perfil do slicer após mudanças", "component": "software", "interval_days": 90},
]


class MaintenanceEventCreate(BaseModel):
    event_type: MaintenanceEventType = "maintenance"
    component: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=1, max_length=120)
    notes: str = Field(default="", max_length=1000)
    performed_at: str | None = Field(default=None, max_length=40)
    print_hours_at: float | None = Field(default=None, ge=0)
    print_hours_read_at: str | None = Field(default=None, max_length=40)


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
    print_hours_at: float | None = None
    print_hours_read_at: str | None = None


class MaintenanceTaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    component: str = Field(min_length=1, max_length=80)
    interval_days: int = Field(default=30, ge=1, le=3650)
    interval_kind: MaintenanceIntervalKind = "days"
    interval_value: float | None = Field(default=None, gt=0, le=100000)
    last_done_at: str | None = Field(default=None, max_length=40)
    last_done_print_hours: float | None = Field(default=None, ge=0)
    last_print_hours_read_at: str | None = Field(default=None, max_length=40)


class MaintenanceTaskComplete(BaseModel):
    notes: str = Field(default="", max_length=1000)
    performed_at: str | None = Field(default=None, max_length=40)
    next_interval_days: int | None = Field(default=None, ge=1, le=3650)
    next_interval_kind: MaintenanceIntervalKind | None = None
    next_interval_value: float | None = Field(default=None, gt=0, le=100000)
    print_hours_at: float | None = Field(default=None, ge=0)
    print_hours_read_at: str | None = Field(default=None, max_length=40)
    disable_reminder: bool = False


class MaintenanceTaskRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    name: str
    component: str
    interval_days: int
    interval_kind: MaintenanceIntervalKind
    interval_value: float
    last_done_at: str | None
    last_done_print_hours: float | None
    last_print_hours_read_at: str | None
    current_print_hours: float | None
    current_print_hours_read_at: str | None
    current_print_hours_source: str | None
    is_active: bool
    created_at: str
    updated_at: str
    due_status: TaskDueStatus
    days_until_due: int | None
    print_hours_delta: float | None = None
    print_hours_until_due: float | None = None
    due_detail: str | None = None


class MaintenanceSummary(BaseModel):
    printer_id: int
    safe_mode: str
    counts: dict[str, int]
    due_components: list[str]
    next_due_task: MaintenanceTaskRecord | None
    recommended_tasks: list[dict[str, Any]]
    print_hours_source: str | None = None
    print_hours_read_at: str | None = None


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
            if payload.print_hours_at is not None or payload.print_hours_read_at is not None:
                connection.execute(
                    """
                    UPDATE maintenance_events
                    SET print_hours_at = ?, print_hours_read_at = ?
                    WHERE id = ?
                    """,
                    (payload.print_hours_at, _clean_timestamp(payload.print_hours_read_at), event_id),
                )
        event = self.get_event(event_id)
        if event is None:
            raise RuntimeError("maintenance event was not persisted")
        return event

    def list_events(self, printer_id: int, limit: int = 50) -> list[MaintenanceEventRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, performed_at, event_type, component, title, notes, created_at,
                       print_hours_at, print_hours_read_at
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
                SELECT id, printer_id, performed_at, event_type, component, title, notes, created_at,
                       print_hours_at, print_hours_read_at
                FROM maintenance_events
                WHERE id = ?
                """,
                (event_id,),
            ).fetchone()
        return _event_from_row(row) if row else None

    def delete_event(self, event_id: int) -> MaintenanceEventRecord | None:
        event = self.get_event(event_id)
        if event is None:
            return None
        with connect_database(self.database_path) as connection:
            connection.execute("DELETE FROM maintenance_events WHERE id = ?", (event.id,))
            self._sync_tasks_for_event(connection, event)
        return event

    def create_task(self, printer_id: int, payload: MaintenanceTaskCreate) -> MaintenanceTaskRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO maintenance_tasks (
                    printer_id, name, component, interval_days, interval_kind, interval_value,
                    last_done_at, last_done_print_hours, last_print_hours_read_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    payload.name.strip(),
                    payload.component.strip(),
                    payload.interval_days,
                    payload.interval_kind,
                    _interval_value(payload.interval_kind, payload.interval_value, payload.interval_days),
                    _clean_timestamp(payload.last_done_at),
                    payload.last_done_print_hours,
                    _clean_timestamp(payload.last_print_hours_read_at),
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
                SELECT id, printer_id, name, component, interval_days, interval_kind, interval_value,
                       last_done_at, last_done_print_hours, last_print_hours_read_at,
                       current_print_hours, current_print_hours_read_at, current_print_hours_source,
                       is_active, created_at, updated_at
                FROM maintenance_tasks
                WHERE printer_id = ?
                ORDER BY is_active DESC, component ASC, name ASC
                """,
                (printer_id,),
            ).fetchall()
        return [_task_from_row(row) for row in rows]

    def summary(self, printer_id: int) -> MaintenanceSummary:
        tasks = self.list_tasks(printer_id)
        counts = {"due": 0, "soon": 0, "ok": 0, "unknown": 0, "inactive": 0}
        for task in tasks:
            if not task.is_active:
                counts["inactive"] += 1
                continue
            counts[task.due_status] += 1
        due_components = sorted(
            {task.component for task in tasks if task.is_active and task.due_status in {"due", "soon"}}
        )
        active_known_tasks = [task for task in tasks if task.is_active and task.due_status not in {"unknown", "not_validated", "needs_review"}]
        next_due_task = min(active_known_tasks, key=_task_due_sort_value) if active_known_tasks else None
        existing = {(task.name.lower(), task.component.lower()) for task in tasks}
        recommended_tasks = [
            task
            for task in DEFAULT_PREVENTIVE_TASKS
            if (str(task["name"]).lower(), str(task["component"]).lower()) not in existing
        ]
        return MaintenanceSummary(
            printer_id=printer_id,
            safe_mode="local_only",
            counts=counts,
            due_components=due_components,
            next_due_task=next_due_task,
            recommended_tasks=recommended_tasks,
        )

    def create_default_tasks(self, printer_id: int) -> list[MaintenanceTaskRecord]:
        created: list[MaintenanceTaskRecord] = []
        existing = {
            (task.name.lower(), task.component.lower())
            for task in self.list_tasks(printer_id)
        }
        for task in DEFAULT_PREVENTIVE_TASKS:
            key = (str(task["name"]).lower(), str(task["component"]).lower())
            if key in existing:
                continue
            created.append(
                self.create_task(
                    printer_id,
                    MaintenanceTaskCreate(
                        name=str(task["name"]),
                        component=str(task["component"]),
                        interval_days=int(task["interval_days"]),
                    ),
                )
            )
            existing.add(key)
        return created

    def ensure_default_tasks(self, printer_id: int) -> None:
        if not self.list_tasks(printer_id):
            self.create_default_tasks(printer_id)

    def get_task(self, task_id: int) -> MaintenanceTaskRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, name, component, interval_days, interval_kind, interval_value,
                       last_done_at, last_done_print_hours, last_print_hours_read_at,
                       current_print_hours, current_print_hours_read_at, current_print_hours_source,
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
        interval_kind = payload.next_interval_kind or task.interval_kind
        interval_value = _complete_interval_value(task, payload)
        print_hours_read_at = _clean_timestamp(payload.print_hours_read_at)
        event = self.create_event(
            task.printer_id,
            MaintenanceEventCreate(
                event_type="maintenance",
                component=task.component,
                title=task.name,
                notes=payload.notes,
                performed_at=performed_at,
                print_hours_at=payload.print_hours_at,
                print_hours_read_at=print_hours_read_at,
            ),
        )
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE maintenance_tasks
                SET last_done_at = ?,
                    interval_days = COALESCE(?, interval_days),
                    interval_kind = ?,
                    interval_value = ?,
                    last_done_print_hours = ?,
                    last_print_hours_read_at = ?,
                    is_active = CASE WHEN ? THEN 0 ELSE 1 END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    performed_at,
                    int(interval_value) if interval_kind == "days" else payload.next_interval_days,
                    interval_kind,
                    interval_value,
                    payload.print_hours_at if interval_kind == "print_hours" else None,
                    print_hours_read_at if interval_kind == "print_hours" else None,
                    1 if payload.disable_reminder else 0,
                    task.id,
                ),
            )
        return event

    def update_current_print_hours(
        self,
        printer_id: int,
        print_hours: float | None,
        *,
        read_at: str | None,
        source: str,
    ) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                UPDATE maintenance_tasks
                SET current_print_hours = COALESCE(?, current_print_hours),
                    current_print_hours_read_at = COALESCE(?, current_print_hours_read_at),
                    current_print_hours_source = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE printer_id = ?
                  AND interval_kind = 'print_hours'
                """,
                (print_hours, _clean_timestamp(read_at), source, printer_id),
            )

    def delete_latest_task_event(self, task_id: int) -> MaintenanceEventRecord | None:
        task = self.get_task(task_id)
        if task is None:
            return None
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, performed_at, event_type, component, title, notes, created_at,
                       print_hours_at, print_hours_read_at
                FROM maintenance_events
                WHERE printer_id = ?
                  AND event_type = 'maintenance'
                  AND lower(title) = lower(?)
                  AND lower(COALESCE(component, '')) = lower(?)
                ORDER BY performed_at DESC, id DESC
                LIMIT 1
                """,
                (task.printer_id, task.name, task.component),
            ).fetchone()
            if row is None:
                return None
            event = _event_from_row(row)
            connection.execute("DELETE FROM maintenance_events WHERE id = ?", (event.id,))
            self._sync_task_last_done(connection, task)
        return event

    def _sync_tasks_for_event(self, connection, event: MaintenanceEventRecord) -> None:
        rows = connection.execute(
            """
            SELECT id, printer_id, name, component, interval_days, interval_kind, interval_value,
                   last_done_at, last_done_print_hours, last_print_hours_read_at,
                   current_print_hours, current_print_hours_read_at, current_print_hours_source,
                   is_active, created_at, updated_at
            FROM maintenance_tasks
            WHERE printer_id = ?
              AND lower(name) = lower(?)
              AND lower(COALESCE(component, '')) = lower(COALESCE(?, ''))
            """,
            (event.printer_id, event.title, event.component),
        ).fetchall()
        for row in rows:
            self._sync_task_last_done(connection, _task_from_row(row))

    def _sync_task_last_done(self, connection, task: MaintenanceTaskRecord) -> None:
        latest = connection.execute(
            """
            SELECT performed_at, print_hours_at, print_hours_read_at
            FROM maintenance_events
            WHERE printer_id = ?
              AND event_type = 'maintenance'
              AND lower(title) = lower(?)
              AND lower(COALESCE(component, '')) = lower(?)
            ORDER BY performed_at DESC, id DESC
            LIMIT 1
            """,
            (task.printer_id, task.name, task.component),
        ).fetchone()
        connection.execute(
            """
            UPDATE maintenance_tasks
            SET last_done_at = ?,
                last_done_print_hours = ?,
                last_print_hours_read_at = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                latest["performed_at"] if latest else None,
                latest["print_hours_at"] if latest else None,
                latest["print_hours_read_at"] if latest else None,
                task.id,
            ),
        )


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
        print_hours_at=row["print_hours_at"],
        print_hours_read_at=row["print_hours_read_at"],
    )


def _task_from_row(row) -> MaintenanceTaskRecord:
    interval_kind: MaintenanceIntervalKind = row["interval_kind"] if row["interval_kind"] in {"days", "print_hours"} else "days"
    interval_value = float(row["interval_value"] if row["interval_value"] is not None else row["interval_days"])
    due_status, days_until_due, print_hours_delta, print_hours_until_due, due_detail = _calculate_due_status(
        interval_kind=interval_kind,
        interval_value=interval_value,
        last_done_at=row["last_done_at"],
        interval_days=int(row["interval_days"]),
        last_done_print_hours=row["last_done_print_hours"],
        current_print_hours=row["current_print_hours"],
        current_print_hours_source=row["current_print_hours_source"],
    )
    return MaintenanceTaskRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        name=str(row["name"]),
        component=str(row["component"]),
        interval_days=int(row["interval_days"]),
        interval_kind=interval_kind,
        interval_value=interval_value,
        last_done_at=row["last_done_at"],
        last_done_print_hours=row["last_done_print_hours"],
        last_print_hours_read_at=row["last_print_hours_read_at"],
        current_print_hours=row["current_print_hours"],
        current_print_hours_read_at=row["current_print_hours_read_at"],
        current_print_hours_source=row["current_print_hours_source"],
        is_active=bool(row["is_active"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        due_status=due_status,
        days_until_due=days_until_due,
        print_hours_delta=print_hours_delta,
        print_hours_until_due=print_hours_until_due,
        due_detail=due_detail,
    )


def _calculate_due_status(
    *,
    interval_kind: MaintenanceIntervalKind,
    interval_value: float,
    last_done_at: str | None,
    interval_days: int,
    last_done_print_hours: float | None,
    current_print_hours: float | None,
    current_print_hours_source: str | None,
) -> tuple[TaskDueStatus, int | None, float | None, float | None, str | None]:
    if interval_kind == "print_hours":
        return _calculate_print_hours_due_status(
            interval_value, last_done_print_hours, current_print_hours, current_print_hours_source
        )
    if not last_done_at:
        return "due", 0, None, None, None
    parsed = _parse_datetime(last_done_at)
    if parsed is None:
        return "unknown", None, None, None, "Data da última execução inválida."
    elapsed_days = (datetime.now(timezone.utc) - parsed).days
    days_until_due = interval_days - elapsed_days
    if days_until_due <= 0:
        return "due", 0, None, None, None
    if days_until_due <= max(1, min(7, interval_days // 5)):
        return "soon", days_until_due, None, None, None
    return "ok", days_until_due, None, None, None


def _calculate_print_hours_due_status(
    interval_value: float,
    last_done_print_hours: float | None,
    current_print_hours: float | None,
    current_print_hours_source: str | None,
) -> tuple[TaskDueStatus, int | None, float | None, float | None, str | None]:
    if last_done_print_hours is None:
        return "not_validated", None, None, None, "Aguardando leitura de horas para validar a base."
    if current_print_hours is None:
        return "not_validated", None, None, None, "Moonraker sem leitura de horas disponível."
    delta = current_print_hours - last_done_print_hours
    if delta < 0:
        return "needs_review", None, delta, None, "Total atual menor que a base salva; histórico pode ter sido resetado."
    hours_until_due = interval_value - delta
    detail = "Leitura de horas ao vivo." if current_print_hours_source == "live" else "Leitura de horas desatualizada."
    if hours_until_due <= 0:
        return "due", None, delta, 0, detail
    if hours_until_due <= max(1.0, min(10.0, interval_value * 0.2)):
        return "soon", None, delta, hours_until_due, detail
    return "ok", None, delta, hours_until_due, detail


def _interval_value(interval_kind: MaintenanceIntervalKind, interval_value: float | None, interval_days: int) -> float:
    if interval_kind == "days":
        return float(interval_value if interval_value is not None else interval_days)
    if interval_value is None:
        raise ValueError("interval_value é obrigatório para lembrete por horas de impressão")
    return float(interval_value)


def _complete_interval_value(task: MaintenanceTaskRecord, payload: MaintenanceTaskComplete) -> float:
    interval_kind = payload.next_interval_kind or task.interval_kind
    if interval_kind == "days":
        return float(payload.next_interval_value or payload.next_interval_days or task.interval_days)
    if payload.next_interval_value is not None:
        return float(payload.next_interval_value)
    if payload.next_interval_days is not None:
        return float(payload.next_interval_days)
    return float(task.interval_value)


def _task_due_sort_value(task: MaintenanceTaskRecord) -> float:
    if task.interval_kind == "print_hours":
        return task.print_hours_until_due if task.print_hours_until_due is not None else float("inf")
    return float(task.days_until_due if task.days_until_due is not None else 999999)


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
