import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict

from app.database import connect_database


ExecutionMode = Literal["read_only", "manual", "gcode_review_required", "blocked_while_printing"]
RiskLevel = Literal["low", "medium", "high"]


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
