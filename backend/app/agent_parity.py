from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel

from app.agent_pairing import AgentJobCreateRequest, AgentJobRecord, AgentPairingRepository
from app.database import connect_database
from app.printers import PrinterRecord


ParityState = Literal["implemented", "blocked", "offline", "cached", "not_supported"]


class RemoteParityFeature(BaseModel):
    key: str
    title: str
    job_type: str | None
    state: ParityState
    safety: Literal["read_only", "dry_run", "blocked"]
    detail: str
    latest_job: AgentJobRecord | None = None


class RemoteParityOverview(BaseModel):
    printer_id: int
    executor: str
    agent_online: bool
    features: list[RemoteParityFeature]


class RemoteParityRunRequest(BaseModel):
    feature_key: str


READ_ONLY_FEATURES = {
    "audit": ("Auditoria read-only", "remote_audit", "Coleta inventário seguro do host/Moonraker."),
    "snapshot": ("Snapshot", "remote_snapshot", "Coleta snapshot Moonraker sanitizado."),
    "health": ("Health", "remote_health", "Coleta estado Klipper/Moonraker e resumo de saúde."),
    "temperatures": ("Temperaturas", "remote_temperatures", "Coleta temperaturas e targets."),
    "update_manager": ("Update Manager", "remote_update_status", "Coleta status read-only do Update Manager."),
    "can": ("CAN", "remote_can_status", "Coleta indicadores CAN read-only quando disponíveis."),
    "final_validation": ("Validação final", "remote_final_validation", "Executa validação final read-only."),
    "sanitized_report": ("Relatório sanitizado", "remote_report_sanitized", "Gera pacote de dados sanitizado no agente."),
}

DRY_RUN_FEATURES = {
    "backup_preview": ("Backup preview", "remote_backup_preview", "Planeja backup sem transferir arquivo grande."),
    "operation_preview": ("Preview operacional", "remote_operation_preview", "Planeja ação operacional sem executar comando mutável."),
    "firmware_preview": ("Firmware preview", "remote_firmware_preview", "Planeja firmware/build/flash sem executar make ou flash."),
}

BLOCKED_FEATURES = {
    "backup_payload": ("Backup real remoto", None, "Bloqueado até política de payload grande e retenção."),
    "firmware_build_apply": ("Build/flash remoto", None, "Bloqueado até gates remotos."),
    "mutable_operation": ("Operação mutável remota", None, "Bloqueado até autorização/preflight."),
}


class AgentParityRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def overview(self, printer: PrinterRecord) -> RemoteParityOverview:
        agent_online = self._has_recent_agent(printer.id)
        features: list[RemoteParityFeature] = []
        for key, (title, job_type, detail) in READ_ONLY_FEATURES.items():
            latest = self._latest_job(printer.id, job_type)
            features.append(_feature(key, title, job_type, "read_only", detail, latest, agent_online))
        for key, (title, job_type, detail) in DRY_RUN_FEATURES.items():
            latest = self._latest_job(printer.id, job_type)
            features.append(_feature(key, title, job_type, "dry_run", detail, latest, agent_online))
        for key, (title, job_type, detail) in BLOCKED_FEATURES.items():
            features.append(
                RemoteParityFeature(
                    key=key,
                    title=title,
                    job_type=job_type,
                    state="blocked",
                    safety="blocked",
                    detail=detail,
                )
            )
        return RemoteParityOverview(
            printer_id=printer.id,
            executor="agent",
            agent_online=agent_online,
            features=features,
        )

    def create_remote_job(self, printer: PrinterRecord, request: RemoteParityRunRequest) -> AgentJobRecord:
        catalog = {**READ_ONLY_FEATURES, **DRY_RUN_FEATURES}
        if request.feature_key in BLOCKED_FEATURES:
            raise ValueError("funcionalidade bloqueada por segurança")
        if request.feature_key not in catalog:
            raise ValueError("funcionalidade remota não suportada")
        _title, job_type, _detail = catalog[request.feature_key]
        return AgentPairingRepository(self.database_path).create_job(
            printer,
            AgentJobCreateRequest(
                job_type=job_type,
                correlation_id=f"parity_{request.feature_key}_{uuid4().hex}",
                payload={"feature_key": request.feature_key, "safe_mode": "read_only_or_dry_run"},
            ),
        )

    def _has_recent_agent(self, printer_id: int) -> bool:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id
                FROM printer_agents
                WHERE printer_id = ?
                  AND status = 'active'
                  AND revoked_at IS NULL
                  AND last_seen_at IS NOT NULL
                  AND last_seen_at >= datetime('now', '-2 minutes')
                LIMIT 1
                """,
                (printer_id,),
            ).fetchone()
        return row is not None

    def _latest_job(self, printer_id: int, job_type: str) -> AgentJobRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM agent_jobs
                WHERE printer_id = ? AND job_type = ? AND status IN ('succeeded', 'failed')
                ORDER BY finished_at DESC, updated_at DESC, id DESC
                LIMIT 1
                """,
                (printer_id, job_type),
            ).fetchone()
        return _job_from_row(row) if row else None


def _feature(
    key: str,
    title: str,
    job_type: str,
    safety: Literal["read_only", "dry_run", "blocked"],
    detail: str,
    latest: AgentJobRecord | None,
    agent_online: bool,
) -> RemoteParityFeature:
    state: ParityState = "implemented" if agent_online else "offline"
    if latest is not None:
        state = "implemented" if agent_online else "cached"
    return RemoteParityFeature(
        key=key,
        title=title,
        job_type=job_type,
        state=state,
        safety=safety,
        detail=detail,
        latest_job=_sanitize_job(latest) if latest else None,
    )


def _sanitize_job(job: AgentJobRecord) -> AgentJobRecord:
    data = job.model_dump()
    data["payload"] = _sanitize_payload(data.get("payload"))
    data["result"] = _sanitize_payload(data.get("result")) if data.get("result") is not None else None
    data["error_message"] = _sanitize_text(data.get("error_message"))
    return AgentJobRecord(**data)


def _sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _sanitize_payload(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value[:50]]
    if isinstance(value, str):
        return _sanitize_text(value)
    return value


def _sanitize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value[:500]
    text = text.replace("PKG-", "entrega-")
    return re.sub(r"ptr_(?:agent|pair|sess)_[A-Za-z0-9_-]+", "[redacted]", text)


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
