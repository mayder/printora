import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

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


class CalibrationSummary(BaseModel):
    printer_id: int
    safe_mode: str
    catalog_count: int
    run_count: int
    category_counts: dict[str, int]
    risk_counts: dict[str, int]
    execution_mode_counts: dict[str, int]
    result_counts: dict[str, int]
    blocked_while_printing_count: int
    gcode_review_required_count: int
    latest_runs: list[CalibrationRunRecord]
    recommended_next_tests: list[dict[str, Any]]


class HiddenCalibrationTest(BaseModel):
    test_key: str
    title: str
    reason: str


class CalibrationAvailableTestsResponse(BaseModel):
    safe_mode: str
    printer_id: int
    data_state: Literal["live", "offline"]
    tests: list[CalibrationTestRecord]
    hidden_tests: list[HiddenCalibrationTest]


class CalibrationSequenceStep(BaseModel):
    order: int
    phase: str
    test_key: str
    title: str
    status: str
    risk_level: RiskLevel
    execution_mode: ExecutionMode
    reason: str


class CalibrationSequencePlan(BaseModel):
    safe_mode: str
    printer_id: int
    total_steps: int
    completed_steps: int
    blocked_while_printing_count: int
    steps: list[CalibrationSequenceStep]


class CalibrationPreflight(BaseModel):
    safe_mode: str
    printer_id: int
    test_key: str
    test_title: str
    data_state: Literal["live", "offline"]
    connected: bool
    printing: bool
    print_state: str
    klipper_state: str | None
    klippy_state: str | None
    blocked: bool
    can_execute_gcode: bool
    block_reasons: list[str]
    checklist: list[str]
    gcode_preview: list[str]
    rollback_plan: str
    summary: str


class CalibrationExecutionRequest(BaseModel):
    test_key: str = Field(min_length=1, max_length=120)
    confirmation: str = Field(default="", max_length=120)
    operator_present: bool = False
    gcode_reviewed: bool = False


class CalibrationExecutionGate(BaseModel):
    status: Literal["ready", "blocked"]
    confirmation_matched: bool
    operator_present: bool
    gcode_reviewed: bool
    connected: bool
    printing: bool
    print_state: str
    klipper_state: str | None
    klippy_state: str | None
    commands: list[str]
    block_reasons: list[str]
    message: str


class CalibrationExecutionRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    test_key: str
    created_at: str
    status: str
    confirmation_matched: bool
    operator_present: bool
    gcode_reviewed: bool
    connected: bool
    printing: bool
    print_state: str
    klipper_state: str | None
    klippy_state: str | None
    commands: list[str]
    sent_commands: list[str]
    result: list[dict[str, Any]]
    block_reasons: list[str]
    message: str


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
        if test.gcode and not payload.gcode_reviewed and payload.result_status != "skipped":
            raise ValueError("gcode_reviewed is required for tests with suggested G-code")
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

    def delete_run_if_not_latest(self, printer_id: int, run_id: int) -> bool:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, test_key
                FROM calibration_test_runs
                WHERE id = ? AND printer_id = ?
                """,
                (run_id, printer_id),
            ).fetchone()
            if row is None:
                return False
            latest = connection.execute(
                """
                SELECT id
                FROM calibration_test_runs
                WHERE printer_id = ? AND test_key = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (printer_id, row["test_key"]),
            ).fetchone()
            if latest is not None and int(latest["id"]) == run_id:
                raise ValueError("não é permitido apagar o último resultado deste teste")
            connection.execute(
                """
                DELETE FROM calibration_test_runs
                WHERE id = ? AND printer_id = ?
                """,
                (run_id, printer_id),
            )
        return True

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

    def summary(self, printer_id: int) -> CalibrationSummary:
        tests = self.list_tests()
        runs = self.list_runs(printer_id, limit=200)
        latest_runs = runs[:8]
        result_counts = {"passed": 0, "warning": 0, "failed": 0, "skipped": 0}
        for run in runs:
            result_counts[run.result_status] += 1
        category_counts = _count_by(tests, "category")
        risk_counts = _count_by(tests, "risk_level")
        execution_mode_counts = _count_by(tests, "execution_mode")
        resolved_keys = {run.test_key for run in runs if run.result_status in {"passed", "skipped"}}
        recommended = [
            {
                "test_key": test.test_key,
                "title": test.title,
                "category": test.category,
                "risk_level": test.risk_level,
                "reason": "Ainda sem resultado aprovado para esta impressora.",
            }
            for test in tests
            if test.test_key not in resolved_keys
        ][:5]
        return CalibrationSummary(
            printer_id=printer_id,
            safe_mode="manual_read_only",
            catalog_count=len(tests),
            run_count=len(runs),
            category_counts=category_counts,
            risk_counts=risk_counts,
            execution_mode_counts=execution_mode_counts,
            result_counts=result_counts,
            blocked_while_printing_count=sum(1 for test in tests if test.blocked_while_printing),
            gcode_review_required_count=sum(1 for test in tests if test.gcode),
            latest_runs=latest_runs,
            recommended_next_tests=recommended,
        )

    def sequence_plan(self, printer_id: int) -> CalibrationSequencePlan:
        tests = self.list_tests()
        runs = self.list_runs(printer_id, limit=500)
        latest_result_by_key: dict[str, CalibrationResultStatus] = {}
        for run in runs:
            latest_result_by_key.setdefault(run.test_key, run.result_status)
        steps = [
            CalibrationSequenceStep(
                order=index + 1,
                phase=_phase_for_test(test),
                test_key=test.test_key,
                title=test.title,
                status=_sequence_status(latest_result_by_key.get(test.test_key)),
                risk_level=test.risk_level,
                execution_mode=test.execution_mode,
                reason=_sequence_reason(test, latest_result_by_key.get(test.test_key)),
            )
            for index, test in enumerate(tests)
        ]
        return CalibrationSequencePlan(
            safe_mode="manual_sequence_no_gcode",
            printer_id=printer_id,
            total_steps=len(steps),
            completed_steps=sum(1 for step in steps if step.status in {"completed", "skipped"}),
            blocked_while_printing_count=sum(1 for test in tests if test.blocked_while_printing),
            steps=steps,
        )

    def create_execution_attempt(
        self,
        *,
        printer_id: int,
        test: CalibrationTestRecord,
        gate: CalibrationExecutionGate,
        status: str,
        sent_commands: list[str],
        result: list[dict[str, Any]],
        message: str,
    ) -> CalibrationExecutionRecord:
        with connect_database(self.database_path) as connection:
            cursor = connection.execute(
                """
                INSERT INTO calibration_execution_attempts (
                    printer_id, test_key, status, confirmation_matched, operator_present,
                    gcode_reviewed, connected, printing, print_state, klipper_state, klippy_state,
                    commands_json, sent_commands_json, result_json, block_reasons_json, message
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    printer_id,
                    test.test_key,
                    status,
                    1 if gate.confirmation_matched else 0,
                    1 if gate.operator_present else 0,
                    1 if gate.gcode_reviewed else 0,
                    1 if gate.connected else 0,
                    1 if gate.printing else 0,
                    gate.print_state,
                    gate.klipper_state,
                    gate.klippy_state,
                    json.dumps(gate.commands, ensure_ascii=False),
                    json.dumps(sent_commands, ensure_ascii=False),
                    json.dumps(result, ensure_ascii=False, sort_keys=True),
                    json.dumps(gate.block_reasons, ensure_ascii=False),
                    message,
                ),
            )
            attempt_id = int(cursor.lastrowid)
        record = self.get_execution_attempt(attempt_id)
        if record is None:
            raise RuntimeError("calibration execution attempt was not persisted")
        return record

    def get_execution_attempt(self, attempt_id: int) -> CalibrationExecutionRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, test_key, created_at, status, confirmation_matched,
                       operator_present, gcode_reviewed, connected, printing, print_state,
                       klipper_state, klippy_state, commands_json, sent_commands_json,
                       result_json, block_reasons_json, message
                FROM calibration_execution_attempts
                WHERE id = ?
                """,
                (attempt_id,),
            ).fetchone()
        return _execution_from_row(row) if row else None

    def list_execution_attempts(self, printer_id: int, limit: int = 20) -> list[CalibrationExecutionRecord]:
        clean_limit = min(max(limit, 1), 100)
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, test_key, created_at, status, confirmation_matched,
                       operator_present, gcode_reviewed, connected, printing, print_state,
                       klipper_state, klippy_state, commands_json, sent_commands_json,
                       result_json, block_reasons_json, message
                FROM calibration_execution_attempts
                WHERE printer_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, clean_limit),
            ).fetchall()
        return [_execution_from_row(row) for row in rows]

    def delete_execution_attempt_if_not_latest(self, printer_id: int, attempt_id: int) -> bool:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, test_key
                FROM calibration_execution_attempts
                WHERE id = ? AND printer_id = ?
                """,
                (attempt_id, printer_id),
            ).fetchone()
            if row is None:
                return False
            latest = connection.execute(
                """
                SELECT id
                FROM calibration_execution_attempts
                WHERE printer_id = ? AND test_key = ?
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (printer_id, row["test_key"]),
            ).fetchone()
            if latest is not None and int(latest["id"]) == attempt_id:
                raise ValueError("não é permitido apagar a última execução deste teste")
            connection.execute(
                """
                DELETE FROM calibration_execution_attempts
                WHERE id = ? AND printer_id = ?
                """,
                (attempt_id, printer_id),
            )
        return True

    def recent_sent_execution(self, printer_id: int, test_key: str, within_seconds: int = 45) -> CalibrationExecutionRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, test_key, created_at, status, confirmation_matched,
                       operator_present, gcode_reviewed, connected, printing, print_state,
                       klipper_state, klippy_state, commands_json, sent_commands_json,
                       result_json, block_reasons_json, message
                FROM calibration_execution_attempts
                WHERE printer_id = ?
                  AND test_key = ?
                  AND status IN ('executed', 'dispatched_unconfirmed', 'failed_partial')
                  AND sent_commands_json != '[]'
                  AND created_at >= datetime('now', ?)
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (printer_id, test_key, f"-{max(1, int(within_seconds))} seconds"),
            ).fetchone()
        return _execution_from_row(row) if row else None


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


def _execution_from_row(row) -> CalibrationExecutionRecord:
    return CalibrationExecutionRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        test_key=str(row["test_key"]),
        created_at=str(row["created_at"]),
        status=str(row["status"]),
        confirmation_matched=bool(row["confirmation_matched"]),
        operator_present=bool(row["operator_present"]),
        gcode_reviewed=bool(row["gcode_reviewed"]),
        connected=bool(row["connected"]),
        printing=bool(row["printing"]),
        print_state=str(row["print_state"]),
        klipper_state=row["klipper_state"],
        klippy_state=row["klippy_state"],
        commands=_json_list(row["commands_json"]),
        sent_commands=_json_list(row["sent_commands_json"]),
        result=_json_dict_list(row["result_json"]),
        block_reasons=_json_list(row["block_reasons_json"]),
        message=str(row["message"]),
    )


def _clean_optional(value: str | None) -> str | None:
    cleaned = value.strip() if value else None
    return cleaned or None


def _count_by(tests: list[CalibrationTestRecord], field_name: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for test in tests:
        value = str(getattr(test, field_name))
        counts[value] = counts.get(value, 0) + 1
    return counts


def _phase_for_test(test: CalibrationTestRecord) -> str:
    mapping = {
        "validacao_mecanica": "01_base_mecanica",
        "mecanica": "01_base_mecanica",
        "temperatura": "02_temperatura",
        "extrusao_base": "03_extrusao_base",
        "probe": "04_probe_mesa",
        "nivelamento": "04_probe_mesa",
        "primeira_camada": "05_primeira_camada",
        "material": "06_material",
        "extrusao": "06_material",
        "movimento": "07_movimento",
        "qualidade": "08_acabamento",
        "dimensional": "09_dimensional",
        "perifericos": "10_perifericos",
    }
    return mapping.get(test.category, f"99_{test.category}")


def _sequence_status(result_status: CalibrationResultStatus | None) -> str:
    if result_status == "passed":
        return "completed"
    if result_status == "skipped":
        return "skipped"
    return "pending"


def _sequence_reason(test: CalibrationTestRecord, result_status: CalibrationResultStatus | None) -> str:
    if result_status == "passed":
        return "Já existe resultado aprovado para esta impressora."
    if result_status == "skipped":
        return "Operador pulou este item; não conta como aprovado."
    if test.gcode:
        return "Pendente: revisar G-code manualmente antes de executar fora do app."
    if test.execution_mode == "read_only":
        return "Pendente: pode ser revisado offline ou por inspeção manual."
    return "Pendente: execução manual, sem envio automático pelo Printora."


def build_available_calibration_tests(
    *,
    printer_id: int,
    tests: list[CalibrationTestRecord],
    available_objects: list[str],
    object_status: dict[str, Any] | None = None,
    connected: bool,
) -> CalibrationAvailableTestsResponse:
    object_names = {name.strip().lower() for name in available_objects if name.strip()}
    visible: list[CalibrationTestRecord] = []
    hidden: list[HiddenCalibrationTest] = []
    for test in tests:
        reason = _unsupported_calibration_reason(test, object_names, object_status or {}, connected=connected)
        if reason:
            hidden.append(HiddenCalibrationTest(test_key=test.test_key, title=test.title, reason=reason))
        else:
            visible.append(test)
    return CalibrationAvailableTestsResponse(
        safe_mode="printer_capability_filtered",
        printer_id=printer_id,
        data_state="live" if connected else "offline",
        tests=visible,
        hidden_tests=hidden,
    )


def _unsupported_calibration_reason(
    test: CalibrationTestRecord,
    object_names: set[str],
    object_status: dict[str, Any],
    *,
    connected: bool,
) -> str | None:
    if not test.gcode:
        return None
    if not connected:
        return "Sem leitura ao vivo das capacidades; testes com G-code ficam ocultos."
    commands = "\n".join(test.gcode).upper()
    if "QUAD_GANTRY_LEVEL" in commands and "quad_gantry_level" not in object_names:
        return "A impressora selecionada não expõe QUAD_GANTRY_LEVEL."
    if "BED_MESH_CALIBRATE" in commands and "bed_mesh" not in object_names:
        return "A impressora selecionada não expõe bed_mesh."
    if "PROBE_ACCURACY" in commands and not _has_probe_object(object_names):
        return "A impressora selecionada não expõe probe."
    if any(command.strip().upper().startswith(("G28", "G0", "G1")) for command in test.gcode) and "toolhead" not in object_names:
        return "A impressora selecionada não expõe toolhead."
    coordinate_reason = _unsupported_coordinate_reason(test.gcode, object_status)
    if coordinate_reason:
        return coordinate_reason
    return None


def _has_probe_object(object_names: set[str]) -> bool:
    return any(name == "probe" or name == "bltouch" or name == "smart_effector" or name.endswith("probe") for name in object_names)


def _unsupported_coordinate_reason(commands: list[str], object_status: dict[str, Any]) -> str | None:
    toolhead = object_status.get("toolhead") if isinstance(object_status, dict) else None
    if not isinstance(toolhead, dict):
        return None
    axis_minimum = _number_list(toolhead.get("axis_minimum"))
    axis_maximum = _number_list(toolhead.get("axis_maximum"))
    if len(axis_minimum) < 3 or len(axis_maximum) < 3:
        return None
    axis_index = {"X": 0, "Y": 1, "Z": 2}
    for command in commands:
        clean_command = command.strip().upper()
        if not clean_command.startswith(("G0", "G1")):
            continue
        for axis, value in re.findall(r"\b([XYZ])\s*(-?\d+(?:\.\d+)?)", clean_command):
            coordinate = float(value)
            index = axis_index[axis]
            if coordinate < axis_minimum[index] or coordinate > axis_maximum[index]:
                return f"Coordenada {axis}{coordinate:g} fora do volume configurado da impressora."
    return None


def _number_list(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    numbers: list[float] = []
    for item in value:
        try:
            numbers.append(float(item))
        except (TypeError, ValueError):
            return []
    return numbers


def build_calibration_preflight(
    *,
    printer_id: int,
    test: CalibrationTestRecord,
    preflight: dict[str, Any],
) -> CalibrationPreflight:
    connected = bool(preflight.get("connected"))
    print_state = str(preflight.get("print_state") or "")
    printing = bool(preflight.get("printing"))
    klipper_state = _optional_text(preflight.get("klipper_state"))
    klippy_state = _optional_text(preflight.get("klippy_state"))
    block_reasons: list[str] = []
    if not connected:
        block_reasons.append("Moonraker/Klipper sem leitura ao vivo.")
    if klipper_state and klipper_state != "ready":
        block_reasons.append(f"Klipper não está ready: {klipper_state}.")
    if klippy_state and klippy_state != "ready":
        block_reasons.append(f"Moonraker reportou Klippy em estado {klippy_state}.")
    if printing and test.blocked_while_printing:
        block_reasons.append("Teste bloqueado porque a impressora está imprimindo.")
    unsupported_reason = _unsupported_calibration_reason(
        test,
        {str(name).strip().lower() for name in preflight.get("available_objects", []) if str(name).strip()},
        preflight.get("object_status", {}) if isinstance(preflight.get("object_status"), dict) else {},
        connected=connected,
    )
    if unsupported_reason:
        block_reasons.append(unsupported_reason)
    blocked_command = _blocked_calibration_command([command.strip() for command in test.gcode if command.strip()])
    if blocked_command:
        block_reasons.append(f"Comando fora da allowlist segura: {blocked_command}.")
    checklist = [
        "Confirmar que a impressora selecionada é a correta.",
        "Confirmar que não há impressão em andamento antes de qualquer calibração.",
        "Ler pré-condições e critérios de sucesso do teste.",
        "Revisar o G-code completo fora do app antes de qualquer execução manual.",
        "Registrar o resultado manual após a validação.",
    ]
    if test.gcode and not block_reasons:
        checklist.append("Executar pelo app somente com operador presente e confirmação explícita.")
    if test.risk_level != "low":
        checklist.append("Tratar este teste como risco elevado e executar somente com supervisão.")

    blocked = bool(block_reasons)
    return CalibrationPreflight(
        safe_mode="read_only_calibration_preflight",
        printer_id=printer_id,
        test_key=test.test_key,
        test_title=test.title,
        data_state="live" if connected else "offline",
        connected=connected,
        printing=printing,
        print_state=print_state,
        klipper_state=klipper_state,
        klippy_state=klippy_state,
        blocked=blocked,
        can_execute_gcode=bool(test.gcode) and not blocked,
        block_reasons=block_reasons,
        checklist=checklist,
        gcode_preview=test.gcode,
        rollback_plan="Nenhum rollback necessário: este preflight não envia G-code e não altera a impressora.",
        summary="Preflight pronto para confirmação supervisionada." if not blocked else "Preflight concluído com bloqueios.",
    )


def build_calibration_execution_gate(
    *,
    test: CalibrationTestRecord,
    payload: CalibrationExecutionRequest,
    preflight: dict[str, Any],
) -> CalibrationExecutionGate:
    connected = bool(preflight.get("connected"))
    printing = bool(preflight.get("printing"))
    print_state = str(preflight.get("print_state") or "")
    klipper_state = _clean_optional(str(preflight.get("klipper_state") or ""))
    klippy_state = _clean_optional(str(preflight.get("klippy_state") or ""))
    confirmation_matched = payload.confirmation.strip() == "EXECUTE_CALIBRATION_GCODE"
    commands = [command.strip() for command in test.gcode if command.strip()]
    block_reasons: list[str] = []
    if not commands:
        block_reasons.append("Teste não possui G-code catalogado para execução.")
    if not confirmation_matched:
        block_reasons.append("Frase de confirmação inválida.")
    if not payload.operator_present:
        block_reasons.append("Operador presente não confirmado.")
    if not payload.gcode_reviewed:
        block_reasons.append("Revisão explícita do G-code não confirmada.")
    if not connected:
        block_reasons.append("Moonraker/Klipper sem leitura ao vivo.")
    if test.blocked_while_printing and printing:
        block_reasons.append("Teste bloqueado porque a impressora está imprimindo.")
    if klipper_state != "ready":
        block_reasons.append(f"Klipper não está ready ({klipper_state or '-'}).")
    if klippy_state != "ready":
        block_reasons.append(f"Klippy não está ready ({klippy_state or '-'}).")
    unsupported_reason = _unsupported_calibration_reason(
        test,
        {str(name).strip().lower() for name in preflight.get("available_objects", []) if str(name).strip()},
        preflight.get("object_status", {}) if isinstance(preflight.get("object_status"), dict) else {},
        connected=connected,
    )
    if unsupported_reason:
        block_reasons.append(unsupported_reason)
    blocked_command = _blocked_calibration_command(commands)
    if blocked_command:
        block_reasons.append(f"Comando fora da allowlist segura: {blocked_command}.")
    return CalibrationExecutionGate(
        status="blocked" if block_reasons else "ready",
        confirmation_matched=confirmation_matched,
        operator_present=payload.operator_present,
        gcode_reviewed=payload.gcode_reviewed,
        connected=connected,
        printing=printing,
        print_state=print_state,
        klipper_state=klipper_state,
        klippy_state=klippy_state,
        commands=commands,
        block_reasons=block_reasons,
        message=(
            "Gate liberado para envio controlado de G-code pelo operador presente."
            if not block_reasons
            else "Execução bloqueada; nenhum G-code foi enviado."
        ),
    )


def _blocked_calibration_command(commands: list[str]) -> str | None:
    allowed_codes = {
        "G28",
        "G0",
        "G1",
        "G90",
        "G91",
        "M82",
        "M83",
        "M106",
        "M107",
        "QUAD_GANTRY_LEVEL",
        "BED_MESH_CALIBRATE",
    }
    allowed_prefixes = (
        "PROBE_ACCURACY",
        "PID_CALIBRATE ",
        "SET_HEATER_TEMPERATURE ",
    )
    denied_prefixes = ("SAVE_CONFIG", "RESTART", "FIRMWARE_RESTART", "M112")
    for command in commands:
        upper = command.strip().upper()
        code = upper.split(maxsplit=1)[0] if upper else ""
        if upper.startswith(denied_prefixes):
            return command
        if code not in allowed_codes and not upper.startswith(allowed_prefixes):
            return command
    return None


def _json_list(value: str) -> list[str]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [str(item) for item in payload] if isinstance(payload, list) else []


def _json_dict_list(value: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return []
    return [item for item in payload if isinstance(item, dict)] if isinstance(payload, list) else []


def _optional_text(value: Any) -> str | None:
    return value if isinstance(value, str) else None
