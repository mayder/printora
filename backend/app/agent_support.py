from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field

from app.agent_pairing import (
    AGENT_PROTOCOL_VERSION,
    EXPECTED_AGENT_VERSION,
    AgentEventRecord,
    AgentJobCreateRequest,
    AgentJobRecord,
    AgentPairingRepository,
    AgentRecord,
)
from app.database import connect_database
from app.printers import PrinterRecord


AgentHealthState = Literal["online", "offline", "revoked", "outdated", "unknown"]
AgentAlertSeverity = Literal["info", "warning", "critical"]


class AgentHealthSummary(BaseModel):
    agent: AgentRecord
    state: AgentHealthState
    online: bool
    heartbeat_age_seconds: int | None
    expected_version: str
    protocol_version: int | None
    protocol_compatible: bool
    pending_jobs: int
    in_progress_jobs: int
    failed_jobs_24h: int
    latest_job: AgentJobRecord | None = None
    latest_failure: AgentJobRecord | None = None
    diagnostic: str


class AgentSupportAlert(BaseModel):
    severity: AgentAlertSeverity
    code: str
    title: str
    detail: str
    action: str


class AgentSupportOverview(BaseModel):
    printer_id: int
    safe_mode: str
    generated_at: str
    retention_days: int
    agents: list[AgentHealthSummary]
    alerts: list[AgentSupportAlert]
    recent_events: list[AgentEventRecord] = Field(default_factory=list)
    latest_doctor: AgentJobRecord | None = None


class AgentSupportBundle(BaseModel):
    printer_id: int
    safe_mode: str
    generated_at: str
    retention_policy: dict[str, Any]
    overview: AgentSupportOverview
    recent_jobs: list[AgentJobRecord]
    support_notes: list[str]


class AgentSupportRepository:
    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path

    def overview(self, printer: PrinterRecord) -> AgentSupportOverview:
        agents = self._agents(printer.id)
        health = [self._agent_health(printer.id, agent) for agent in agents]
        return AgentSupportOverview(
            printer_id=printer.id,
            safe_mode="agent_support_sanitized",
            generated_at=_now_text(),
            retention_days=180,
            agents=health,
            alerts=_alerts(health),
            recent_events=self._events(printer.id),
            latest_doctor=self._latest_doctor(printer.id),
        )

    def create_doctor_job(self, printer: PrinterRecord) -> AgentJobRecord:
        return AgentPairingRepository(self.database_path).create_job(
            printer,
            AgentJobCreateRequest(
                job_type="remote_doctor",
                correlation_id=f"remote_doctor_{uuid4().hex}",
                payload={"safe_mode": "support_diagnostics", "requested_at": _now_text()},
            ),
        )

    def support_bundle(self, printer: PrinterRecord) -> AgentSupportBundle:
        overview = self.overview(printer)
        return AgentSupportBundle(
            printer_id=printer.id,
            safe_mode="support_bundle_sanitized",
            generated_at=_now_text(),
            retention_policy={
                "events_days": 180,
                "jobs_days": 180,
                "cleanup": "manual por rotina operacional documentada; nenhum dado é apagado automaticamente por este endpoint",
            },
            overview=overview,
            recent_jobs=[_sanitize_job(job) for job in self._recent_jobs(printer.id, 30)],
            support_notes=[
                "Revogar ou rotacionar credencial se houver suspeita de comprometimento.",
                "Reinstalar o agente se não houver heartbeat recente.",
                "Atualizar o agente quando a versão estiver diferente da versão esperada.",
                "Validar Moonraker/Klipper localmente se o doctor remoto falhar nesses checks.",
            ],
        )

    def _agent_health(self, printer_id: int, agent: AgentRecord) -> AgentHealthSummary:
        pending_jobs = self._job_count(printer_id, agent.id, "pending")
        in_progress_jobs = self._job_count(printer_id, agent.id, "in_progress")
        failed_jobs_24h = self._failed_jobs_24h(printer_id, agent.id)
        latest_job = self._latest_job(printer_id, agent.id)
        latest_failure = self._latest_failure(printer_id, agent.id)
        age_seconds = _age_seconds(agent.last_seen_at)
        online = bool(agent.status == "active" and age_seconds is not None and age_seconds <= 120)
        protocol_version = _int_or_none(agent.capabilities.get("protocol_v"))
        protocol_compatible = protocol_version in {None, AGENT_PROTOCOL_VERSION}
        state = _health_state(agent, online)
        return AgentHealthSummary(
            agent=agent,
            state=state,
            online=online,
            heartbeat_age_seconds=age_seconds,
            expected_version=EXPECTED_AGENT_VERSION,
            protocol_version=protocol_version,
            protocol_compatible=protocol_compatible,
            pending_jobs=pending_jobs,
            in_progress_jobs=in_progress_jobs,
            failed_jobs_24h=failed_jobs_24h,
            latest_job=_sanitize_job(latest_job) if latest_job else None,
            latest_failure=_sanitize_job(latest_failure) if latest_failure else None,
            diagnostic=_diagnostic(agent, state, protocol_compatible, pending_jobs, failed_jobs_24h),
        )

    def _agents(self, printer_id: int) -> list[AgentRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                "SELECT * FROM printer_agents WHERE printer_id = ? ORDER BY last_seen_at DESC, paired_at DESC, id DESC",
                (printer_id,),
            ).fetchall()
        return [_agent_from_row(row) for row in rows]

    def _events(self, printer_id: int) -> list[AgentEventRecord]:
        return AgentPairingRepository(self.database_path).list_events(printer_id, limit=40)

    def _recent_jobs(self, printer_id: int, limit: int) -> list[AgentJobRecord]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM agent_jobs
                WHERE printer_id = ?
                ORDER BY created_at DESC, id DESC
                LIMIT ?
                """,
                (printer_id, max(1, min(limit, 100))),
            ).fetchall()
        return [_job_from_row(row) for row in rows]

    def _latest_doctor(self, printer_id: int) -> AgentJobRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM agent_jobs
                WHERE printer_id = ? AND job_type = 'remote_doctor'
                ORDER BY created_at DESC, id DESC
                LIMIT 1
                """,
                (printer_id,),
            ).fetchone()
        return _sanitize_job(_job_from_row(row)) if row else None

    def _latest_job(self, printer_id: int, agent_id: int) -> AgentJobRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM agent_jobs
                WHERE printer_id = ? AND agent_id = ?
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
                """,
                (printer_id, agent_id),
            ).fetchone()
        return _job_from_row(row) if row else None

    def _latest_failure(self, printer_id: int, agent_id: int) -> AgentJobRecord | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT *
                FROM agent_jobs
                WHERE printer_id = ? AND agent_id = ? AND status = 'failed'
                ORDER BY updated_at DESC, id DESC
                LIMIT 1
                """,
                (printer_id, agent_id),
            ).fetchone()
        return _job_from_row(row) if row else None

    def _job_count(self, printer_id: int, agent_id: int, status: str) -> int:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM agent_jobs
                WHERE printer_id = ? AND (agent_id IS NULL OR agent_id = ?) AND status = ?
                """,
                (printer_id, agent_id, status),
            ).fetchone()
        return int(row["total"]) if row else 0

    def _failed_jobs_24h(self, printer_id: int, agent_id: int) -> int:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS total
                FROM agent_jobs
                WHERE printer_id = ? AND agent_id = ? AND status = 'failed'
                  AND updated_at >= datetime('now', '-1 day')
                """,
                (printer_id, agent_id),
            ).fetchone()
        return int(row["total"]) if row else 0


def _alerts(health: list[AgentHealthSummary]) -> list[AgentSupportAlert]:
    alerts: list[AgentSupportAlert] = []
    if not health:
        alerts.append(_alert("critical", "agent_missing", "Nenhum agente pareado", "Instale ou pareie o agente nesta impressora.", "Gerar instalação assistida."))
    for item in health:
        agent_label = item.agent.stable_id
        if item.agent.status == "revoked":
            alerts.append(_alert("warning", "agent_revoked", "Agente revogado", f"{agent_label} está revogado.", "Parear novo agente ou rotacionar credencial."))
        elif not item.online:
            alerts.append(_alert("critical", "agent_offline", "Agente sem heartbeat", f"{agent_label} não enviou heartbeat recente.", "Validar serviço printora-agent no host."))
        if item.agent.agent_version != EXPECTED_AGENT_VERSION:
            alerts.append(_alert("warning", "agent_outdated", "Agente desatualizado", f"{agent_label} usa {item.agent.agent_version or '-'}; esperado {EXPECTED_AGENT_VERSION}.", "Executar update do agente."))
        if not item.protocol_compatible:
            alerts.append(_alert("critical", "protocol_incompatible", "Protocolo incompatível", f"{agent_label} reportou protocolo {item.protocol_version}.", "Atualizar agente antes de novos jobs."))
        if item.pending_jobs >= 5:
            alerts.append(_alert("warning", "queue_accumulated", "Fila acumulada", f"{agent_label} tem {item.pending_jobs} jobs pendentes.", "Verificar conectividade e WebSocket/polling."))
        if item.failed_jobs_24h >= 3:
            alerts.append(_alert("warning", "recurring_failures", "Falha recorrente", f"{agent_label} teve {item.failed_jobs_24h} falhas em 24h.", "Rodar doctor remoto e revisar última falha."))
    return alerts


def _alert(severity: AgentAlertSeverity, code: str, title: str, detail: str, action: str) -> AgentSupportAlert:
    return AgentSupportAlert(severity=severity, code=code, title=title, detail=detail, action=action)


def _diagnostic(agent: AgentRecord, state: AgentHealthState, protocol_compatible: bool, pending_jobs: int, failed_jobs_24h: int) -> str:
    if agent.status == "revoked":
        return "Agente revogado; não deve receber jobs."
    if state == "offline":
        return "Sem heartbeat recente; validar serviço, rede e credencial local."
    if not protocol_compatible:
        return "Protocolo incompatível; atualizar agente antes de operar."
    if pending_jobs >= 5:
        return "Fila acumulada; verificar canal WebSocket/polling e API."
    if failed_jobs_24h >= 3:
        return "Falhas recorrentes; executar doctor remoto."
    if agent.agent_version != EXPECTED_AGENT_VERSION:
        return "Agente responde, mas versão está diferente da esperada."
    return "Agente saudável."


def _health_state(agent: AgentRecord, online: bool) -> AgentHealthState:
    if agent.status == "revoked":
        return "revoked"
    if not online:
        return "offline"
    if agent.agent_version != EXPECTED_AGENT_VERSION:
        return "outdated"
    return "online"


def _sanitize_job(job: AgentJobRecord) -> AgentJobRecord:
    data = job.model_dump()
    data["payload"] = _sanitize_payload(data.get("payload"))
    data["result"] = _sanitize_payload(data.get("result")) if data.get("result") is not None else None
    data["error_message"] = _sanitize_text(data.get("error_message"))
    return AgentJobRecord(**data)


def _sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            lower = str(key).lower()
            if any(secret in lower for secret in ("password", "token", "secret", "credential", "private_key")):
                cleaned[str(key)] = "[redacted]"
            else:
                cleaned[str(key)] = _sanitize_payload(item)
        return cleaned
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value[:50]]
    if isinstance(value, str):
        return _sanitize_text(value)
    return value


def _sanitize_text(value: str | None) -> str | None:
    if value is None:
        return None
    text = value[:500]
    for marker in ("ptr_agent_", "ptr_pair_", "ptr_sess_"):
        if marker in text:
            text = text.replace(marker, marker + "[redacted]")
    return text


def _age_seconds(value: str | None) -> int | None:
    if not value:
        return None
    parsed = _parse_dt(value)
    if parsed is None:
        return None
    return max(0, int((datetime.now(timezone.utc) - parsed).total_seconds()))


def _parse_dt(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return None


def _now_text() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def _agent_from_row(row) -> AgentRecord:
    return AgentRecord(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        stable_id=str(row["stable_id"]),
        credential_prefix=str(row["credential_prefix"]),
        agent_version=row["agent_version"],
        platform=row["platform"],
        capabilities=json.loads(row["capabilities_json"] or "{}"),
        status=row["status"],
        paired_at=str(row["paired_at"]),
        last_seen_at=row["last_seen_at"],
        revoked_at=row["revoked_at"],
        rotated_at=row["rotated_at"],
    )


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
