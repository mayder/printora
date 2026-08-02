from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


ReconstructionStatus = Literal["queued", "processing", "succeeded", "failed", "cancelled"]
ReconstructionStage = Literal[
    "waiting",
    "preparing",
    "camera_poses",
    "dense_cloud",
    "surface",
    "packaging",
    "ready",
    "failed",
    "cancelled",
]
EnginePolicy = Literal["auto", "local", "provider"]


class ReconstructionCreate(BaseModel):
    capture_session_id: int = Field(gt=0)
    engine_policy: EnginePolicy = "auto"


class ReconstructionArtifact(BaseModel):
    id: int
    artifact_type: Literal["raw_mesh", "preview", "coverage"]
    file_format: str
    sha256: str
    size_bytes: int
    unit: str
    observed_ratio: float | None
    inferred_ratio: float | None
    provenance: dict[str, object]


class ReconstructionAttempt(BaseModel):
    id: int
    attempt_number: int
    engine_key: str
    adapter_version: str
    status: str
    stage: str
    estimated_cost_cents: int | None
    actual_cost_cents: int | None
    started_at: str
    completed_at: str | None


class ReconstructionJob(BaseModel):
    id: int
    capture_session_id: int
    project_id: int
    status: ReconstructionStatus
    stage: ReconstructionStage
    progress_percent: int | None
    engine_policy: EnginePolicy
    engine_key: str | None
    correlation_id: str
    error_code: str | None
    error_message: str | None
    estimated_cost_cents: int | None
    actual_cost_cents: int | None
    can_cancel: bool
    can_retry: bool
    next_action: str
    created_at: str
    updated_at: str
    attempts: list[ReconstructionAttempt]
    artifacts: list[ReconstructionArtifact]
