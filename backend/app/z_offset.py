from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.database import connect_database


ZOffsetAlertLevel = Literal["ok", "monitorar", "revisar"]


class ZOffsetRecordCreate(BaseModel):
    plate_name: str = Field(default="Texturizada", min_length=1, max_length=80)
    material: str = Field(default="PLA", min_length=1, max_length=40)
    nozzle: str = Field(default="T0", min_length=1, max_length=40)
    offset_value: float = Field(ge=-10.0, le=10.0)
    notes: str = Field(default="", max_length=1000)
    recorded_at: str | None = Field(default=None, max_length=40)


class ZOffsetRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    recorded_at: str
    plate_name: str
    material: str
    nozzle: str
    offset_value: float
    previous_offset_value: float | None
    delta_value: float | None
    alert_level: ZOffsetAlertLevel
    notes: str
    created_at: str


class ZOffsetWizardStep(BaseModel):
    key: str
    title: str
    detail: str
    command: str | None = None
    must_confirm: bool = True


class ZOffsetWizardPlan(BaseModel):
    safe_mode: str
    plate_name: str
    material: str
    nozzle: str
    proposed_offset_value: float
    previous_offset_value: float | None
    delta_value: float | None
    alert_level: ZOffsetAlertLevel
    recommendation: str
    can_save_record: bool
    steps: list[ZOffsetWizardStep]


@dataclass(frozen=True)
class ZOffsetRepository:
    database_path: Path

    def create_record(self, printer_id: int, payload: ZOffsetRecordCreate) -> ZOffsetRecord:
        plate_name = payload.plate_name.strip()
        material = payload.material.strip().upper()
        nozzle = payload.nozzle.strip().upper()
        previous = self.latest_matching_record(printer_id, plate_name, material, nozzle)
        previous_value = previous.offset_value if previous else None
        delta = payload.offset_value - previous_value if previous_value is not None else None
        alert_level = _alert_level(delta)
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO z_offset_records (
                    printer_id, recorded_at, plate_name, material, nozzle, offset_value,
                    previous_offset_value, delta_value, alert_level, notes
                )
                VALUES (?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    _clean_optional(payload.recorded_at),
                    plate_name,
                    material,
                    nozzle,
                    payload.offset_value,
                    previous_value,
                    delta,
                    alert_level,
                    payload.notes.strip(),
                ),
            )
            record_id = int(cursor.lastrowid)
        record = self.get_record(record_id)
        if record is None:
            raise RuntimeError("z-offset record was not persisted")
        return record

    def list_records(self, printer_id: int, limit: int = 50) -> list[ZOffsetRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, recorded_at, plate_name, material, nozzle, offset_value,
                       previous_offset_value, delta_value, alert_level, notes, created_at
                FROM z_offset_records
                WHERE printer_id = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, limit),
            ).fetchall()
        return [_record_from_row(row) for row in rows]

    def get_record(self, record_id: int) -> ZOffsetRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, recorded_at, plate_name, material, nozzle, offset_value,
                       previous_offset_value, delta_value, alert_level, notes, created_at
                FROM z_offset_records
                WHERE id = ?
                """,
                (record_id,),
            ).fetchone()
        return _record_from_row(row) if row else None

    def latest_matching_record(
        self,
        printer_id: int,
        plate_name: str,
        material: str,
        nozzle: str,
    ) -> ZOffsetRecord | None:
        clean_plate = plate_name.strip()
        clean_material = material.strip().upper()
        clean_nozzle = nozzle.strip().upper()
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, recorded_at, plate_name, material, nozzle, offset_value,
                       previous_offset_value, delta_value, alert_level, notes, created_at
                FROM z_offset_records
                WHERE printer_id = ? AND plate_name = ? AND material = ? AND nozzle = ?
                ORDER BY recorded_at DESC, id DESC
                LIMIT 1
                """,
                (printer_id, clean_plate, clean_material, clean_nozzle),
            ).fetchone()
        return _record_from_row(row) if row else None


def build_z_offset_wizard_plan(
    plate_name: str,
    material: str,
    nozzle: str,
    proposed_offset_value: float,
    previous_record: ZOffsetRecord | None,
) -> ZOffsetWizardPlan:
    previous_value = previous_record.offset_value if previous_record else None
    delta = proposed_offset_value - previous_value if previous_value is not None else None
    alert_level = _alert_level(delta)
    return ZOffsetWizardPlan(
        safe_mode="manual_guided_no_gcode",
        plate_name=plate_name.strip(),
        material=material.strip().upper(),
        nozzle=nozzle.strip().upper(),
        proposed_offset_value=proposed_offset_value,
        previous_offset_value=previous_value,
        delta_value=delta,
        alert_level=alert_level,
        recommendation=_wizard_recommendation(alert_level, delta),
        can_save_record=True,
        steps=[
            ZOffsetWizardStep(
                key="precheck",
                title="Preparar impressora",
                detail="Confirme mesa limpa, nozzle limpo, filamento sem pressão no bico e impressora parada.",
            ),
            ZOffsetWizardStep(
                key="home",
                title="Fazer homing manualmente",
                detail="Execute o homing pela interface da impressora antes da calibração.",
                command="G28",
            ),
            ZOffsetWizardStep(
                key="probe_calibrate",
                title="Abrir calibração manual",
                detail="Execute este comando no console e ajuste com papel até chegar ao ponto correto.",
                command="PROBE_CALIBRATE",
            ),
            ZOffsetWizardStep(
                key="accept",
                title="Aceitar valor calibrado",
                detail="Depois do ajuste físico, aceite o valor na janela de calibração.",
                command="ACCEPT",
            ),
            ZOffsetWizardStep(
                key="record",
                title="Registrar no MayderPrintLab",
                detail="Copie o valor final e salve neste histórico. Este app não altera printer.cfg.",
            ),
        ],
    )


def _record_from_row(row) -> ZOffsetRecord:
    return ZOffsetRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        recorded_at=str(row["recorded_at"]),
        plate_name=str(row["plate_name"]),
        material=str(row["material"]),
        nozzle=str(row["nozzle"]),
        offset_value=float(row["offset_value"]),
        previous_offset_value=float(row["previous_offset_value"]) if row["previous_offset_value"] is not None else None,
        delta_value=float(row["delta_value"]) if row["delta_value"] is not None else None,
        alert_level=row["alert_level"],
        notes=str(row["notes"]),
        created_at=str(row["created_at"]),
    )


def _alert_level(delta: float | None) -> ZOffsetAlertLevel:
    if delta is None:
        return "ok"
    absolute_delta = abs(delta)
    if absolute_delta >= 0.1:
        return "revisar"
    if absolute_delta >= 0.05:
        return "monitorar"
    return "ok"


def _wizard_recommendation(alert_level: ZOffsetAlertLevel, delta: float | None) -> str:
    if delta is None:
        return "Sem valor anterior compatível. Salve como referência inicial para esta chapa/material/nozzle."
    if alert_level == "revisar":
        return "Variação alta. Revise limpeza da mesa, fixação da chapa, nozzle, toolhead e probe antes de imprimir."
    if alert_level == "monitorar":
        return "Variação moderada. Pode salvar, mas faça uma primeira camada curta de validação."
    return "Variação pequena. Pode salvar como novo valor de referência."


def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None
