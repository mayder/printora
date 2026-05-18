from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.database import connect_database


CanAlertLevel = Literal["ok", "monitorar", "problema"]


class CanBusRecordCreate(BaseModel):
    interface_name: str = Field(default="can0", min_length=1, max_length=40)
    rx_error: int = Field(default=0, ge=0)
    tx_error: int = Field(default=0, ge=0)
    tx_retries: int = Field(default=0, ge=0)
    bus_state: str | None = Field(default=None, max_length=80)
    bitrate: int | None = Field(default=None, ge=1)
    notes: str = Field(default="", max_length=1000)
    recorded_at: str | None = Field(default=None, max_length=40)


class CanBusRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    recorded_at: str
    interface_name: str
    rx_error: int
    tx_error: int
    tx_retries: int
    bus_state: str | None
    bitrate: int | None
    previous_rx_error: int | None
    previous_tx_error: int | None
    previous_tx_retries: int | None
    delta_rx_error: int | None
    delta_tx_error: int | None
    delta_tx_retries: int | None
    alert_level: CanAlertLevel
    notes: str
    created_at: str


@dataclass(frozen=True)
class CanMonitorRepository:
    database_path: Path

    def create_record(self, printer_id: int, payload: CanBusRecordCreate) -> CanBusRecord:
        interface_name = payload.interface_name.strip()
        previous = self.latest_matching_record(printer_id, interface_name)
        previous_rx = previous.rx_error if previous else None
        previous_tx = previous.tx_error if previous else None
        previous_retries = previous.tx_retries if previous else None
        delta_rx = _delta(payload.rx_error, previous_rx)
        delta_tx = _delta(payload.tx_error, previous_tx)
        delta_retries = _delta(payload.tx_retries, previous_retries)
        alert_level = _alert_level(delta_rx, delta_tx, delta_retries, payload.rx_error, payload.tx_error)

        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO can_bus_records (
                    printer_id, recorded_at, interface_name, rx_error, tx_error, tx_retries,
                    bus_state, bitrate, previous_rx_error, previous_tx_error, previous_tx_retries,
                    delta_rx_error, delta_tx_error, delta_tx_retries, alert_level, notes
                )
                VALUES (?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    _clean_optional(payload.recorded_at),
                    interface_name,
                    payload.rx_error,
                    payload.tx_error,
                    payload.tx_retries,
                    _clean_optional(payload.bus_state),
                    payload.bitrate,
                    previous_rx,
                    previous_tx,
                    previous_retries,
                    delta_rx,
                    delta_tx,
                    delta_retries,
                    alert_level,
                    payload.notes.strip(),
                ),
            )
            record_id = int(cursor.lastrowid)
        record = self.get_record(record_id)
        if record is None:
            raise RuntimeError("CAN record was not persisted")
        return record

    def list_records(self, printer_id: int, limit: int = 50) -> list[CanBusRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, recorded_at, interface_name, rx_error, tx_error, tx_retries,
                       bus_state, bitrate, previous_rx_error, previous_tx_error, previous_tx_retries,
                       delta_rx_error, delta_tx_error, delta_tx_retries, alert_level, notes, created_at
                FROM can_bus_records
                WHERE printer_id = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, limit),
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def get_record(self, record_id: int) -> CanBusRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, recorded_at, interface_name, rx_error, tx_error, tx_retries,
                       bus_state, bitrate, previous_rx_error, previous_tx_error, previous_tx_retries,
                       delta_rx_error, delta_tx_error, delta_tx_retries, alert_level, notes, created_at
                FROM can_bus_records
                WHERE id = ?
                """,
                (record_id,),
            ).fetchone()
        return _record_from_row(row) if row else None

    def latest_matching_record(self, printer_id: int, interface_name: str) -> CanBusRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, recorded_at, interface_name, rx_error, tx_error, tx_retries,
                       bus_state, bitrate, previous_rx_error, previous_tx_error, previous_tx_retries,
                       delta_rx_error, delta_tx_error, delta_tx_retries, alert_level, notes, created_at
                FROM can_bus_records
                WHERE printer_id = ? AND interface_name = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT 1
                """,
                (printer_id, interface_name.strip()),
            ).fetchone()
        return _record_from_row(row) if row else None


def _record_from_row(row) -> CanBusRecord:
    return CanBusRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        recorded_at=str(row["recorded_at"]),
        interface_name=str(row["interface_name"]),
        rx_error=int(row["rx_error"]),
        tx_error=int(row["tx_error"]),
        tx_retries=int(row["tx_retries"]),
        bus_state=row["bus_state"],
        bitrate=int(row["bitrate"]) if row["bitrate"] is not None else None,
        previous_rx_error=int(row["previous_rx_error"]) if row["previous_rx_error"] is not None else None,
        previous_tx_error=int(row["previous_tx_error"]) if row["previous_tx_error"] is not None else None,
        previous_tx_retries=int(row["previous_tx_retries"]) if row["previous_tx_retries"] is not None else None,
        delta_rx_error=int(row["delta_rx_error"]) if row["delta_rx_error"] is not None else None,
        delta_tx_error=int(row["delta_tx_error"]) if row["delta_tx_error"] is not None else None,
        delta_tx_retries=int(row["delta_tx_retries"]) if row["delta_tx_retries"] is not None else None,
        alert_level=row["alert_level"],
        notes=str(row["notes"]),
        created_at=str(row["created_at"]),
    )


def _delta(current: int, previous: int | None) -> int | None:
    return current - previous if previous is not None else None


def _alert_level(
    delta_rx_error: int | None,
    delta_tx_error: int | None,
    delta_tx_retries: int | None,
    rx_error: int,
    tx_error: int,
) -> CanAlertLevel:
    if (delta_rx_error and delta_rx_error > 0) or (delta_tx_error and delta_tx_error > 0):
        return "problema"
    if delta_tx_retries and delta_tx_retries > 0:
        return "monitorar"
    if rx_error > 0 or tx_error > 0:
        return "monitorar"
    return "ok"


def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None
