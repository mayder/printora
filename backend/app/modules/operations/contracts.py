from __future__ import annotations

from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

AGENT_PROTOCOL_VERSION = 1


AGENT_MAX_PAYLOAD_BYTES = 64 * 1024


AGENT_MAX_RESULT_BYTES = 512 * 1024


EXPECTED_AGENT_VERSION = "0.1.33"


AgentStatus = Literal["active", "revoked", "removed"]


AgentJobStatus = Literal["pending", "in_progress", "succeeded", "failed", "canceled"]


AgentMessageType = Literal["hello", "heartbeat", "snapshot", "job", "ack", "nack", "result", "error", "backpressure"]


class AgentPairingConflictError(ValueError):
    def __init__(self, stable_id: str) -> None:
        self.stable_id = stable_id
        super().__init__(
            f"Este host já está pareado como {stable_id}. "
            "Revogue/remova o agente antigo antes de reinstalar."
        )


class PairingTokenCreateRequest(BaseModel):
    ttl_minutes: int = Field(default=15, ge=1, le=60)


class PairingTokenResponse(BaseModel):
    id: int
    printer_id: int
    token: str
    token_prefix: str
    expires_at: str
    created_at: str


class AgentInstallPlanResponse(BaseModel):
    printer_id: int
    token_id: int
    token_prefix: str
    expires_at: str
    expected_agent_version: str
    script_url: str
    preflight_command: str
    install_command: str
    uninstall_command: str


class PairingTokenRecord(BaseModel):
    id: int
    printer_id: int
    token_prefix: str
    status: Literal["active", "used", "revoked", "expired", "removed"]
    expires_at: str
    created_at: str
    consumed_at: str | None = None
    revoked_at: str | None = None
    removed_at: str | None = None


class AgentExchangeRequest(BaseModel):
    pairing_token: str = Field(min_length=20, max_length=240)
    stable_id: str = Field(min_length=3, max_length=160)
    agent_version: str | None = Field(default=None, max_length=80)
    platform: str | None = Field(default=None, max_length=120)
    capabilities: dict[str, Any] = Field(default_factory=dict)

    @field_validator("stable_id")
    @classmethod
    def clean_stable_id(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("identidade do agente é obrigatória")
        return cleaned


class AgentCredentialExchangeResponse(BaseModel):
    agent_id: int
    printer_id: int
    credential: str
    credential_prefix: str
    status: AgentStatus


class AgentRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    printer_id: int
    stable_id: str
    credential_prefix: str
    agent_version: str | None
    platform: str | None
    capabilities: dict[str, Any]
    status: AgentStatus
    paired_at: str
    last_seen_at: str | None
    revoked_at: str | None
    removed_at: str | None = None
    rotated_at: str | None


class AgentPairingOverview(BaseModel):
    printer_id: int
    pairing_tokens: list[PairingTokenRecord]
    agents: list[AgentRecord]


class AgentInstallStatusResponse(BaseModel):
    printer_id: int
    expected_agent_version: str
    ready: bool
    active_agents: int
    latest_agent_id: int | None = None
    latest_stable_id: str | None = None
    latest_version: str | None = None
    latest_platform: str | None = None
    latest_last_seen_at: str | None = None
    diagnostic: str


class AgentHeartbeatRequest(BaseModel):
    agent_version: str | None = Field(default=None, max_length=80)
    platform: str | None = Field(default=None, max_length=120)
    capabilities: dict[str, Any] = Field(default_factory=dict)


class AgentHeartbeatResponse(BaseModel):
    accepted: bool
    agent_id: int
    printer_id: int
    status: AgentStatus


class AgentSnapshotRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentProtocolMessage(BaseModel):
    protocol_version: int = AGENT_PROTOCOL_VERSION
    message_type: AgentMessageType
    correlation_id: str = Field(default_factory=lambda: f"msg_{uuid4().hex}", min_length=3, max_length=120)
    payload: dict[str, Any] = Field(default_factory=dict)


class AgentJobCreateRequest(BaseModel):
    job_type: str = Field(min_length=2, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)
    agent_id: int | None = None
    correlation_id: str | None = Field(default=None, min_length=3, max_length=120)
    expires_at: str | None = None


class AgentJobRecord(BaseModel):
    id: int
    printer_id: int
    agent_id: int | None
    correlation_id: str
    job_type: str
    payload: dict[str, Any]
    status: AgentJobStatus
    attempts: int
    result: dict[str, Any] | None = None
    error_message: str | None = None
    created_at: str
    updated_at: str
    acked_at: str | None = None
    finished_at: str | None = None


class AgentJobResponse(BaseModel):
    protocol_version: int = AGENT_PROTOCOL_VERSION
    jobs: list[AgentJobRecord] = Field(default_factory=list)


class AgentJobResultRequest(BaseModel):
    correlation_id: str = Field(min_length=3, max_length=120)
    result: dict[str, Any] = Field(default_factory=dict)


class AgentJobErrorRequest(BaseModel):
    correlation_id: str = Field(min_length=3, max_length=120)
    error_message: str = Field(min_length=1, max_length=500)
    result: dict[str, Any] = Field(default_factory=dict)


class AgentEventRecord(BaseModel):
    id: int
    printer_id: int
    agent_id: int | None
    event_type: str
    status: str
    detail: str | None
    created_at: str

