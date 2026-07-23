from __future__ import annotations

import json
import re
import shlex
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
from app.agent_updates import load_agent_update_manifest
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


class AgentUpdateRequestResponse(BaseModel):
    mode: Literal["remote_job"]
    status: Literal["queued"]
    detail: str
    websocket_delivered: bool = False
    job: AgentJobRecord | None = None


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

    def request_agent_update(
        self,
        printer: PrinterRecord,
        agent_id: int,
        public_base_url: str | None = None,
        channel: Literal["stable", "candidate", "rollback"] = "stable",
    ) -> AgentUpdateRequestResponse:
        agent = next((item for item in self._agents(printer.id) if item.id == agent_id), None)
        if agent is None:
            raise ValueError("agente não pertence à impressora")
        if agent.status != "active":
            raise ValueError("agente precisa estar ativo para receber update remoto")
        manifest = load_agent_update_manifest(public_base_url)
        target_version = manifest.recommended_version
        if channel == "candidate":
            if not manifest.candidate_version:
                raise ValueError("release candidata indisponível")
            target_version = manifest.candidate_version
        release = _release_for_version(manifest, target_version)
        if agent.platform not in (None, release.platform):
            raise ValueError(f"release {release.platform} incompatível com agente {agent.platform}")
        if channel == "rollback" and _version_tuple(agent.agent_version) <= _version_tuple(target_version):
            raise ValueError("rollback exige agente em versão superior à recomendada")
        job_type = "remote_agent_update_check"
        payload: dict[str, Any] = {
            "safe_mode": "agent_self_update",
            "requested_at": _now_text(),
            "target_version": target_version,
            "update_channel": channel,
        }
        if channel != "stable" or _needs_bootstrap_update(agent.agent_version):
            job_type = "remote_host_script"
            payload = {
                "safe_mode": "agent_update_bootstrap",
                "kind": "agent_update_bootstrap",
                "script": _bootstrap_update_script(
                    release.url,
                    release.sha256,
                    release.signature,
                    agent.agent_version,
                    target_version,
                ),
                "timeout_seconds": 120,
                "target_version": target_version,
                "update_channel": channel,
            }
        job = AgentPairingRepository(self.database_path).create_job(
            printer,
            AgentJobCreateRequest(
                agent_id=agent_id,
                job_type=job_type,
                correlation_id=f"remote_agent_update_{uuid4().hex}",
                payload=payload,
            ),
        )
        return AgentUpdateRequestResponse(
            mode="remote_job",
            status="queued",
            detail=(
                f"{channel.capitalize()} {target_version} registrado para o agente. "
                "A aplicação ocorre pelo próprio serviço, sem SSH."
            ),
            job=job,
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
            agent=_sanitize_agent(agent),
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
                """
                SELECT *
                FROM printer_agents
                WHERE printer_id = ? AND status != 'removed' AND removed_at IS NULL
                ORDER BY last_seen_at DESC, paired_at DESC, id DESC
                """,
                (printer_id,),
            ).fetchall()
        return [_agent_from_row(row) for row in rows]

    def _events(self, printer_id: int) -> list[AgentEventRecord]:
        return [_sanitize_event(event) for event in AgentPairingRepository(self.database_path).list_events(printer_id, limit=40)]

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
            continue
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


def _sanitize_agent(agent: AgentRecord) -> AgentRecord:
    return agent.model_copy(update={"credential_prefix": "[redacted]"})


def _sanitize_event(event: AgentEventRecord) -> AgentEventRecord:
    return event.model_copy(update={"detail": _sanitize_text(event.detail)})


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
    return re.sub(r"ptr_(?:agent|pair|sess)_[A-Za-z0-9_-]+", "[redacted]", text)


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


def _needs_bootstrap_update(agent_version: str | None) -> bool:
    return _version_tuple(agent_version) < (0, 1, 15)


def _version_tuple(version: str | None) -> tuple[int, int, int]:
    parts = str(version or "0.0.0").strip().lstrip("v").split(".")
    values: list[int] = []
    for part in parts[:3]:
        try:
            values.append(int(part))
        except ValueError:
            values.append(0)
    while len(values) < 3:
        values.append(0)
    return values[0], values[1], values[2]


def _release_for_version(manifest, version: str):
    for release in manifest.releases:
        if release.platform == "linux/arm64" and release.version == version:
            return release
    raise ValueError(f"release linux/arm64 {version} indisponível para atualização remota")


_ED25519_VERIFY_PYTHON = r"""
import base64
import hashlib
import sys

PUBLIC_KEY = base64.b64decode("dK8RtUcm2hdrv0CFCNMFago1e+8RmT3ab9fbDyK8hmg=")
FIELD = 2**255 - 19
ORDER = 2**252 + 27742317777372353535851937790883648493


def inverse(value):
    return pow(value, FIELD - 2, FIELD)


D = (-121665 * inverse(121666)) % FIELD
SQRT_M1 = pow(2, (FIELD - 1) // 4, FIELD)


def recover_x(y):
    xx = (y * y - 1) * inverse(D * y * y + 1)
    x = pow(xx, (FIELD + 3) // 8, FIELD)
    if (x * x - xx) % FIELD:
        x = (x * SQRT_M1) % FIELD
    if (x * x - xx) % FIELD:
        raise ValueError("ponto Ed25519 inválido")
    return x


def decode_point(encoded):
    if len(encoded) != 32:
        raise ValueError("ponto Ed25519 inválido")
    y = int.from_bytes(encoded, "little") & ((1 << 255) - 1)
    if y >= FIELD:
        raise ValueError("ponto Ed25519 não canônico")
    x = recover_x(y)
    if (x & 1) != (encoded[31] >> 7):
        x = FIELD - x
    if (-x * x + y * y - 1 - D * x * x * y * y) % FIELD:
        raise ValueError("ponto Ed25519 fora da curva")
    return x, y


def add_points(left, right):
    x1, y1 = left
    x2, y2 = right
    product = D * x1 * x2 * y1 * y2
    return (
        (x1 * y2 + x2 * y1) * inverse(1 + product) % FIELD,
        (y1 * y2 + x1 * x2) * inverse(1 - product) % FIELD,
    )


def multiply_point(point, scalar):
    result = (0, 1)
    current = point
    while scalar:
        if scalar & 1:
            result = add_points(result, current)
        current = add_points(current, current)
        scalar >>= 1
    return result


BASE_Y = 4 * inverse(5) % FIELD
BASE_X = recover_x(BASE_Y)
if BASE_X & 1:
    BASE_X = FIELD - BASE_X
BASE_POINT = (BASE_X, BASE_Y)

message = open(sys.argv[1], "rb").read()
signature = open(sys.argv[2], "rb").read()
if len(signature) != 64:
    raise SystemExit("assinatura Ed25519 inválida")
try:
    public_point = decode_point(PUBLIC_KEY)
    signature_point = decode_point(signature[:32])
except ValueError as error:
    raise SystemExit(str(error)) from error
scalar = int.from_bytes(signature[32:], "little")
if scalar >= ORDER:
    raise SystemExit("assinatura Ed25519 não canônica")
challenge = int.from_bytes(
    hashlib.sha512(signature[:32] + PUBLIC_KEY + message).digest(),
    "little",
) % ORDER
if multiply_point(BASE_POINT, scalar) != add_points(
    signature_point,
    multiply_point(public_point, challenge),
):
    raise SystemExit("assinatura Ed25519 não confere")
""".strip()


def _bootstrap_update_script(
    url: str,
    sha256: str,
    signature: str,
    source_version: str | None,
    target_version: str,
) -> str:
    safe_source = re.sub(r"[^0-9A-Za-z._-]", "-", source_version or "unknown")
    safe_target = re.sub(r"[^0-9A-Za-z._-]", "-", target_version)
    return f"""set -euo pipefail
current_sha="$(sha256sum /usr/local/bin/printora-agent | awk '{{print $1}}')"
if [ "$current_sha" = {shlex.quote(sha256)} ]; then
  echo 'agente já está no artefato alvo {safe_target}'
  exit 0
fi
state="$(curl -4 -fsSL --connect-timeout 5 --max-time 10 \
  'http://127.0.0.1:7125/printer/objects/query?print_stats' |
  python3 -c 'import json,sys; print(json.load(sys.stdin).get("result",{{}}).get("status",{{}}).get("print_stats",{{}}).get("state",""))')"
case "$state" in standby|complete|cancelled|error) ;; *)
  echo "update bloqueado: print_stats.state=${{state:-indisponível}}" >&2
  exit 23
esac
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
curl -4 -fsSL --retry 5 --retry-delay 2 --connect-timeout 10 {shlex.quote(url)} -o "$work/agent"
echo {shlex.quote(sha256 + "  ")}"$work/agent" | sha256sum -c -
printf '%s' {shlex.quote(signature)} | openssl base64 -d -A -out "$work/signature.bin"
printf '%s' {shlex.quote(sha256)} > "$work/digest.txt"
python3 - "$work/digest.txt" "$work/signature.bin" <<'PY'
{_ED25519_VERIFY_PYTHON}
PY
install -d -m 0700 /var/lib/printora-agent/updates
install -m 0755 /usr/local/bin/printora-agent \
  /var/lib/printora-agent/updates/printora-agent.backup-{safe_source}
install -m 0755 "$work/agent" /usr/local/bin/printora-agent.new
mv -f /usr/local/bin/printora-agent.new /usr/local/bin/printora-agent
nohup sh -c 'sleep 1; systemctl restart printora-agent' >/dev/null 2>&1 &
echo 'agente preparado para {safe_target}; restart exclusivo agendado'
"""


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
        removed_at=row["removed_at"],
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
