from dataclasses import dataclass
from pathlib import Path
import re
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


class CanBusParseRequest(BaseModel):
    interface_name: str = Field(default="can0", min_length=1, max_length=40)
    output: str = Field(min_length=1, max_length=8000)


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
    diagnosis: str
    recommended_actions: list[str]
    notes: str
    created_at: str


class CanInterfaceSummary(BaseModel):
    interface_name: str
    latest_alert: CanAlertLevel
    record_count: int
    latest_recorded_at: str
    rx_error: int
    tx_error: int
    tx_retries: int
    delta_rx_error: int | None
    delta_tx_error: int | None
    delta_tx_retries: int | None
    diagnosis: str


class CanBusSummary(BaseModel):
    printer_id: int
    safe_mode: str
    data_state: Literal["manual_records", "no_data"]
    source: str
    counts: dict[str, int]
    interfaces: list[CanInterfaceSummary]
    overall_alert: CanAlertLevel
    recommended_actions: list[str]


class CanBusRecordComparison(BaseModel):
    safe_mode: str
    printer_id: int
    interface_name: str
    before_record_id: int
    after_record_id: int
    delta_rx_error: int
    delta_tx_error: int
    delta_tx_retries: int
    alert_level: CanAlertLevel
    diagnosis: str
    recommended_actions: list[str]


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
        alert_level = _alert_level(delta_rx, delta_tx, delta_retries, payload.rx_error, payload.tx_error, payload.bus_state)

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

    def summary(self, printer_id: int) -> CanBusSummary:
        records = self.list_records(printer_id, limit=200)
        counts = {"ok": 0, "monitorar": 0, "problema": 0}
        latest_by_interface: dict[str, CanBusRecord] = {}
        count_by_interface: dict[str, int] = {}
        for record in records:
            counts[record.alert_level] += 1
            count_by_interface[record.interface_name] = count_by_interface.get(record.interface_name, 0) + 1
            latest_by_interface.setdefault(record.interface_name, record)
        interfaces = [
            CanInterfaceSummary(
                interface_name=record.interface_name,
                latest_alert=record.alert_level,
                record_count=count_by_interface[record.interface_name],
                latest_recorded_at=record.recorded_at,
                rx_error=record.rx_error,
                tx_error=record.tx_error,
                tx_retries=record.tx_retries,
                delta_rx_error=record.delta_rx_error,
                delta_tx_error=record.delta_tx_error,
                delta_tx_retries=record.delta_tx_retries,
                diagnosis=record.diagnosis,
            )
            for record in latest_by_interface.values()
        ]
        overall_alert = _overall_alert([record.alert_level for record in latest_by_interface.values()])
        return CanBusSummary(
            printer_id=printer_id,
            safe_mode="manual_read_only",
            data_state="manual_records" if records else "no_data",
            source="local_can_bus_records",
            counts=counts,
            interfaces=interfaces,
            overall_alert=overall_alert,
            recommended_actions=_recommended_actions(overall_alert),
        )

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

    def compare_records(self, printer_id: int, before_record_id: int, after_record_id: int) -> CanBusRecordComparison:
        before = self.get_record(before_record_id)
        after = self.get_record(after_record_id)
        if before is None or after is None:
            raise ValueError("CAN record not found")
        if before.printer_id != printer_id or after.printer_id != printer_id:
            raise ValueError("CAN records must belong to the selected printer")
        if before.interface_name != after.interface_name:
            raise ValueError("CAN records must use the same interface")
        delta_rx = after.rx_error - before.rx_error
        delta_tx = after.tx_error - before.tx_error
        delta_retries = after.tx_retries - before.tx_retries
        alert_level = _alert_level(delta_rx, delta_tx, delta_retries, after.rx_error, after.tx_error, after.bus_state)
        return CanBusRecordComparison(
            safe_mode="manual_read_only_comparison",
            printer_id=printer_id,
            interface_name=after.interface_name,
            before_record_id=before.id,
            after_record_id=after.id,
            delta_rx_error=delta_rx,
            delta_tx_error=delta_tx,
            delta_tx_retries=delta_retries,
            alert_level=alert_level,
            diagnosis=_diagnosis(alert_level, delta_rx, delta_tx, delta_retries, after.bus_state),
            recommended_actions=_recommended_actions(alert_level),
        )


def _record_from_row(row) -> CanBusRecord:
    alert_level = row["alert_level"]
    delta_rx = int(row["delta_rx_error"]) if row["delta_rx_error"] is not None else None
    delta_tx = int(row["delta_tx_error"]) if row["delta_tx_error"] is not None else None
    delta_retries = int(row["delta_tx_retries"]) if row["delta_tx_retries"] is not None else None
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
        delta_rx_error=delta_rx,
        delta_tx_error=delta_tx,
        delta_tx_retries=delta_retries,
        alert_level=alert_level,
        diagnosis=_diagnosis(alert_level, delta_rx, delta_tx, delta_retries, row["bus_state"]),
        recommended_actions=_recommended_actions(alert_level),
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
    bus_state: str | None = None,
) -> CanAlertLevel:
    clean_state = bus_state.upper() if bus_state else None
    if clean_state and clean_state not in {"ERROR-ACTIVE", "UP"}:
        return "problema"
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


def parse_ip_link_can_output(payload: CanBusParseRequest) -> CanBusRecordCreate:
    output = payload.output
    interface_name = _match_text(output, r"\d+:\s*([^:@\s]+)") or payload.interface_name
    state = _match_text(output, r"can state ([A-Z-]+)")
    bitrate = _match_int(output, r"\bbitrate\s+(\d+)\b")
    rx_error = _match_int(output, r"RX:.*?\n\s*\d+\s+\d+\s+(\d+)", flags=re.DOTALL)
    tx_error = _match_int(output, r"TX:.*?\n\s*\d+\s+\d+\s+(\d+)", flags=re.DOTALL)
    tx_retries = _match_int(output, r"re-started\s+bus-errors\s+arbitration-lost\s+error-warn\s+error-pass\s+bus-off.*?\n\s*\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+(\d+)", flags=re.DOTALL)
    if tx_retries is None:
        tx_retries = _match_int(output, r"\bretries[:=]\s*(\d+)\b")
    return CanBusRecordCreate(
        interface_name=interface_name,
        rx_error=rx_error or 0,
        tx_error=tx_error or 0,
        tx_retries=tx_retries or 0,
        bus_state=state,
        bitrate=bitrate,
        notes="Leitura extraída de saída ip link colada manualmente.",
    )


def _diagnosis(
    alert_level: CanAlertLevel,
    delta_rx_error: int | None,
    delta_tx_error: int | None,
    delta_tx_retries: int | None,
    bus_state: str | None = None,
) -> str:
    clean_state = bus_state.upper() if bus_state else None
    if clean_state and clean_state not in {"ERROR-ACTIVE", "UP"}:
        return f"Estado CAN não está ativo: {bus_state}."
    if alert_level == "problema":
        return f"Contadores de erro CAN aumentaram: rx={delta_rx_error or 0}, tx={delta_tx_error or 0}."
    if alert_level == "monitorar":
        return f"Retransmissões ou erros acumulados exigem acompanhamento: retries={delta_tx_retries or 0}."
    return "Sem crescimento de erro detectado na comparação registrada."


def _recommended_actions(alert_level: CanAlertLevel) -> list[str]:
    if alert_level == "problema":
        return [
            "Não iniciar impressão longa antes de revisar o barramento CAN.",
            "Verificar cabo, crimpagem, alimentação do toolhead, terminação de 120 ohms e aterramento.",
            "Comparar nova leitura após inspeção física, sem zerar contadores.",
        ]
    if alert_level == "monitorar":
        return [
            "Registrar nova leitura depois de movimentar/aquecer a máquina.",
            "Observar se tx_retries continua crescendo na mesma interface.",
        ]
    return ["Manter histórico e comparar novamente após manutenção, update ou impressão longa."]


def _overall_alert(alerts: list[CanAlertLevel]) -> CanAlertLevel:
    if "problema" in alerts:
        return "problema"
    if "monitorar" in alerts:
        return "monitorar"
    return "ok"


def _match_text(text: str, pattern: str, flags: int = 0) -> str | None:
    match = re.search(pattern, text, flags)
    return match.group(1).strip() if match else None


def _match_int(text: str, pattern: str, flags: int = 0) -> int | None:
    value = _match_text(text, pattern, flags)
    return int(value) if value is not None and value.isdigit() else None
