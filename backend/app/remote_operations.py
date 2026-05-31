from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.agent_pairing import AgentJobCreateRequest, AgentJobRecord, AgentPairingRepository
from app.auth import AuthUser, format_dt, utc_now
from app.database import connect_database
from app.operation import _operation_action, _operation_action_commands, _normalize_action_parameters
from app.printers import PrinterRecord


RemoteOperationCriticality = Literal["low", "high", "critical"]
RemoteOperationJobStatus = Literal["pending", "in_progress", "succeeded", "failed", "canceled"]

PREFLIGHT_JOB_TYPE = "remote_mutation_preflight"
EXECUTE_JOB_TYPE = "remote_mutation_execute"
PREFLIGHT_TTL_MINUTES = 10
EXECUTE_TTL_MINUTES = 5


class RemoteOperationAction(BaseModel):
    action_id: str
    label: str
    risk: str
    criticality: RemoteOperationCriticality
    confirmation_required: bool
    blocks_when_printing: bool
    rollback_plan: list[str]


class RemoteOperationOverview(BaseModel):
    printer_id: int
    safe_mode: str
    actions: list[RemoteOperationAction]
    recent_jobs: list[AgentJobRecord] = Field(default_factory=list)


class RemoteOperationPreflightRequest(BaseModel):
    action_id: str = Field(min_length=2, max_length=80)
    parameters: dict[str, Any] = Field(default_factory=dict)


class RemoteOperationExecuteRequest(BaseModel):
    preflight_job_id: int
    confirmation_phrase: str = Field(min_length=3, max_length=120)


class RemoteOperationCancelResponse(BaseModel):
    job: AgentJobRecord
    canceled: bool


class RemoteOperationRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def overview(self, printer: PrinterRecord) -> RemoteOperationOverview:
        return RemoteOperationOverview(
            printer_id=printer.id,
            safe_mode="remote_mutation_guarded",
            actions=[_remote_action(item) for item in _supported_actions()],
            recent_jobs=self._recent_jobs(printer.id),
        )

    def create_preflight(self, printer: PrinterRecord, user: AuthUser, request: RemoteOperationPreflightRequest) -> AgentJobRecord:
        action = _remote_action_by_id(request.action_id)
        parameters = _normalize_action_parameters(action.action_id, request.parameters)
        command_preview = _operation_action_commands(action.action_id, parameters)
        expires_at = format_dt(utc_now() + timedelta(minutes=PREFLIGHT_TTL_MINUTES))
        confirmation_phrase = f"CONFIRM_REMOTE_{action.action_id.upper()}_{uuid4().hex[:8]}"
        payload = {
            "safe_mode": "remote_preflight_only",
            "action_id": action.action_id,
            "action_label": action.label,
            "risk": action.risk,
            "criticality": action.criticality,
            "parameters": parameters,
            "command_preview": command_preview,
            "confirmation_phrase": confirmation_phrase,
            "blocks_when_printing": action.blocks_when_printing,
            "rollback_plan": action.rollback_plan,
            "requested_by": {"user_id": user.id, "email": user.email},
            "expires_at": expires_at,
        }
        return AgentPairingRepository(self.database_path).create_job(
            printer,
            AgentJobCreateRequest(
                job_type=PREFLIGHT_JOB_TYPE,
                correlation_id=f"remote_preflight_{uuid4().hex}",
                payload=payload,
                expires_at=expires_at,
            ),
        )

    def create_execution(self, printer: PrinterRecord, user: AuthUser, request: RemoteOperationExecuteRequest) -> AgentJobRecord:
        preflight = self._job(printer.id, request.preflight_job_id)
        if preflight is None or preflight.job_type != PREFLIGHT_JOB_TYPE:
            raise ValueError("preflight remoto não encontrado")
        if preflight.status != "succeeded":
            raise ValueError("preflight remoto precisa estar aprovado antes da execução")
        if _is_expired(str(preflight.payload.get("expires_at") or preflight.finished_at or preflight.created_at)):
            raise ValueError("preflight remoto expirado")
        result = preflight.result or {}
        if result.get("can_execute") is not True:
            raise ValueError("preflight remoto bloqueou a execução")
        if result.get("printing") is True:
            raise ValueError("impressão em andamento bloqueia operação remota crítica")
        expected_phrase = str(preflight.payload.get("confirmation_phrase") or "")
        if request.confirmation_phrase.strip() != expected_phrase:
            raise ValueError("confirmação forte inválida")
        expires_at = format_dt(utc_now() + timedelta(minutes=EXECUTE_TTL_MINUTES))
        payload = {
            "safe_mode": "remote_mutation_confirmed",
            "preflight_job_id": preflight.id,
            "action_id": preflight.payload.get("action_id"),
            "action_label": preflight.payload.get("action_label"),
            "risk": preflight.payload.get("risk"),
            "criticality": preflight.payload.get("criticality"),
            "parameters": preflight.payload.get("parameters") or {},
            "command_preview": preflight.payload.get("command_preview") or [],
            "rollback_plan": preflight.payload.get("rollback_plan") or [],
            "confirmed_by": {"user_id": user.id, "email": user.email},
            "preflight_result": result,
            "expires_at": expires_at,
        }
        return AgentPairingRepository(self.database_path).create_job(
            printer,
            AgentJobCreateRequest(
                job_type=EXECUTE_JOB_TYPE,
                correlation_id=f"remote_execute_{uuid4().hex}",
                payload=payload,
                expires_at=expires_at,
            ),
        )

    def cancel_job(self, printer: PrinterRecord, job_id: int) -> RemoteOperationCancelResponse:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM agent_jobs
                WHERE id = ? AND printer_id = ? AND job_type IN (?, ?)
                """,
                (job_id, printer.id, PREFLIGHT_JOB_TYPE, EXECUTE_JOB_TYPE),
            ).fetchone()
            if row is None:
                raise ValueError("job remoto não encontrado")
            if row["status"] == "in_progress":
                raise ValueError("job remoto já está em execução no agente")
            if row["status"] == "pending":
                connection.execute(
                    """
                    UPDATE agent_jobs
                    SET status = 'canceled', finished_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP,
                        error_message = 'cancelado pelo usuário antes da execução'
                    WHERE id = ? AND status = 'pending'
                    """,
                    (job_id,),
                )
                connection.execute(
                    """
                    INSERT INTO printer_agent_events (printer_id, agent_id, event_type, status, detail)
                    VALUES (?, ?, 'remote_job_cancel', 'canceled', ?)
                    """,
                    (printer.id, row["agent_id"], str(row["correlation_id"])[:160]),
                )
            updated = connection.execute("SELECT * FROM agent_jobs WHERE id = ?", (job_id,)).fetchone()
        return RemoteOperationCancelResponse(job=_job_from_row(updated), canceled=updated["status"] == "canceled")

    def _job(self, printer_id: int, job_id: int) -> AgentJobRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM agent_jobs
                WHERE id = ? AND printer_id = ? AND job_type IN (?, ?)
                """,
                (job_id, printer_id, PREFLIGHT_JOB_TYPE, EXECUTE_JOB_TYPE),
            ).fetchone()
        return _job_from_row(row) if row else None

    def _recent_jobs(self, printer_id: int) -> list[AgentJobRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM agent_jobs
                WHERE printer_id = ? AND job_type IN (?, ?)
                ORDER BY created_at DESC, id DESC
                LIMIT 20
                """,
                (printer_id, PREFLIGHT_JOB_TYPE, EXECUTE_JOB_TYPE),
            ).fetchall()
        return [_job_from_row(row) for row in rows]


def _supported_actions() -> list[dict[str, Any]]:
    return [
        action
        for action in (_operation_action(action_id) for action_id in _ACTION_CRITICALITY)
        if action is not None
    ]


def _remote_action_by_id(action_id: str) -> RemoteOperationAction:
    action = _operation_action(action_id)
    if action is None or action_id not in _ACTION_CRITICALITY:
        raise ValueError("operação remota mutável não suportada")
    return _remote_action(action)


def _remote_action(action: dict[str, Any]) -> RemoteOperationAction:
    action_id = str(action["id"])
    return RemoteOperationAction(
        action_id=action_id,
        label=str(action["label"]),
        risk=str(action["risk"]),
        criticality=_ACTION_CRITICALITY[action_id],
        confirmation_required=True,
        blocks_when_printing=True,
        rollback_plan=_ROLLBACK_BY_RISK.get(str(action["risk"]), _ROLLBACK_BY_RISK["default"]),
    )


def _is_expired(expires_at: str) -> bool:
    return bool(expires_at) and expires_at <= format_dt(utc_now())


def _job_from_row(row) -> AgentJobRecord:
    return AgentJobRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        agent_id=int(row["agent_id"]) if row["agent_id"] is not None else None,
        correlation_id=str(row["correlation_id"]),
        job_type=str(row["job_type"]),
        payload=json.loads(row["payload_json"] or "{}"),
        status=row["status"],
        attempts=int(row["attempts"]),
        result=json.loads(row["result_json"]) if row["result_json"] else None,
        error_message=row["error_message"],
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        acked_at=row["acked_at"],
        finished_at=row["finished_at"],
    )


_ACTION_CRITICALITY: dict[str, RemoteOperationCriticality] = {
    "home_xyz": "critical",
    "quad_gantry_level": "critical",
    "move_xy": "high",
    "move_absolute": "critical",
    "move_z": "critical",
    "extrude": "high",
    "set_hotend_temp": "high",
    "set_bed_temp": "high",
    "set_fan": "low",
    "set_led": "low",
    "set_speed_factor": "high",
    "set_velocity_limit": "critical",
    "set_extrusion_factor": "high",
    "set_pressure_advance": "high",
}

_ROLLBACK_BY_RISK: dict[str, list[str]] = {
    "heat_toolhead": ["Enviar TARGET=0 para o hotend.", "Usar Emergency Stop se houver aquecimento inesperado."],
    "heat_bed": ["Enviar TARGET=0 para a mesa.", "Usar Emergency Stop se houver aquecimento inesperado."],
    "change_fan": ["Enviar M107 ou SPEED=0 para o fan alterado."],
    "change_led": ["Enviar SET_LED com brilho 0 para o LED alterado."],
    "default": ["Usar Emergency Stop no Mainsail/Klipper se houver comportamento inesperado.", "Revalidar printer/info depois da ação."],
}
