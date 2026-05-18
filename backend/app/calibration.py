import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.database import connect_database


ExecutionMode = Literal["read_only", "manual", "gcode_review_required", "blocked_while_printing"]
RiskLevel = Literal["low", "medium", "high"]
CalibrationResultStatus = Literal["passed", "warning", "failed", "skipped"]


class CalibrationTestRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_key: str
    category: str
    title: str
    objective: str
    source: str
    execution_mode: ExecutionMode
    risk_level: RiskLevel
    blocked_while_printing: bool
    prerequisites: list[str]
    gcode: list[str]
    success_criteria: list[str]
    notes: str
    sort_order: int


class CalibrationRunCreate(BaseModel):
    test_key: str = Field(min_length=1, max_length=120)
    result_status: CalibrationResultStatus
    material: str = Field(default="", max_length=80)
    plate_name: str = Field(default="", max_length=80)
    nozzle: str = Field(default="", max_length=40)
    observed_value: str = Field(default="", max_length=120)
    notes: str = Field(default="", max_length=1000)
    gcode_reviewed: bool = False
    photo_reference: str | None = Field(default=None, max_length=240)


class CalibrationRunRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    test_key: str
    test_title: str
    created_at: str
    result_status: CalibrationResultStatus
    material: str
    plate_name: str
    nozzle: str
    observed_value: str
    notes: str
    gcode_reviewed: bool
    photo_reference: str | None


@dataclass(frozen=True)
class CalibrationRepository:
    database_path: Path

    def list_tests(self, category: str | None = None) -> list[CalibrationTestRecord]:
        query = """
            SELECT id, test_key, category, title, objective, source, execution_mode, risk_level,
                   blocked_while_printing, prerequisites_json, gcode_json, success_criteria_json,
                   notes, sort_order
            FROM calibration_tests
        """
        params: tuple[str, ...] = ()
        if category:
            query += " WHERE category = ?"
            params = (category,)
        query += " ORDER BY sort_order ASC, title ASC"
        with connect_database(self.database_path) as connection:
            rows = connection.execute(query, params).fetchall()
        return [_record_from_row(row) for row in rows]

    def get_test(self, test_key: str) -> CalibrationTestRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, test_key, category, title, objective, source, execution_mode, risk_level,
                       blocked_while_printing, prerequisites_json, gcode_json, success_criteria_json,
                       notes, sort_order
                FROM calibration_tests
                WHERE test_key = ?
                """,
                (test_key,),
            ).fetchone()
        return _record_from_row(row) if row else None

    def create_run(self, printer_id: int, payload: CalibrationRunCreate) -> CalibrationRunRecord:
        test = self.get_test(payload.test_key)
        if test is None:
            raise ValueError("calibration test not found")
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO calibration_test_runs (
                    printer_id, test_key, result_status, material, plate_name, nozzle,
                    observed_value, notes, gcode_reviewed, photo_reference
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    payload.test_key,
                    payload.result_status,
                    payload.material.strip(),
                    payload.plate_name.strip(),
                    payload.nozzle.strip(),
                    payload.observed_value.strip(),
                    payload.notes.strip(),
                    1 if payload.gcode_reviewed else 0,
                    _clean_optional(payload.photo_reference),
                ),
            )
            run_id = int(cursor.lastrowid)
        record = self.get_run(run_id)
        if record is None:
            raise RuntimeError("calibration run was not persisted")
        return record

    def list_runs(self, printer_id: int, limit: int = 50) -> list[CalibrationRunRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT r.id, r.printer_id, r.test_key, t.title AS test_title, r.created_at,
                       r.result_status, r.material, r.plate_name, r.nozzle, r.observed_value,
                       r.notes, r.gcode_reviewed, r.photo_reference
                FROM calibration_test_runs r
                JOIN calibration_tests t ON t.test_key = r.test_key
                WHERE r.printer_id = ?
                ORDER BY r.created_at DESC, r.id DESC
                LIMIT ?
                """,
                (printer_id, limit),
            ).fetchall()
        return [_run_from_row(row) for row in rows]

    def get_run(self, run_id: int) -> CalibrationRunRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT r.id, r.printer_id, r.test_key, t.title AS test_title, r.created_at,
                       r.result_status, r.material, r.plate_name, r.nozzle, r.observed_value,
                       r.notes, r.gcode_reviewed, r.photo_reference
                FROM calibration_test_runs r
                JOIN calibration_tests t ON t.test_key = r.test_key
                WHERE r.id = ?
                """,
                (run_id,),
            ).fetchone()
        return _run_from_row(row) if row else None


def _record_from_row(row) -> CalibrationTestRecord:
    return CalibrationTestRecord(
        id=int(row["id"]),
        test_key=str(row["test_key"]),
        category=str(row["category"]),
        title=str(row["title"]),
        objective=str(row["objective"]),
        source=str(row["source"]),
        execution_mode=row["execution_mode"],
        risk_level=row["risk_level"],
        blocked_while_printing=bool(row["blocked_while_printing"]),
        prerequisites=json.loads(row["prerequisites_json"]),
        gcode=json.loads(row["gcode_json"]),
        success_criteria=json.loads(row["success_criteria_json"]),
        notes=str(row["notes"]),
        sort_order=int(row["sort_order"]),
    )


def _run_from_row(row) -> CalibrationRunRecord:
    return CalibrationRunRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        test_key=str(row["test_key"]),
        test_title=str(row["test_title"]),
        created_at=str(row["created_at"]),
        result_status=row["result_status"],
        material=str(row["material"]),
        plate_name=str(row["plate_name"]),
        nozzle=str(row["nozzle"]),
        observed_value=str(row["observed_value"]),
        notes=str(row["notes"]),
        gcode_reviewed=bool(row["gcode_reviewed"]),
        photo_reference=row["photo_reference"],
    )


def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None
