from __future__ import annotations

from typing import Literal
import re

from pydantic import BaseModel, Field, field_validator


class SanitizedEventCreate(BaseModel):
    event_id: str = Field(min_length=8, max_length=160)
    event_type: Literal[
        "impact.observed",
        "moderation.content_submitted",
        "moderation.report.created",
        "recommendation.signal",
        "geometry.indexed",
        "subject.removal_requested",
    ]
    schema_version: int = Field(default=1, ge=1, le=10)
    purpose: Literal[
        "product_impact",
        "safety_moderation",
        "recommendation",
        "geometry_search",
    ]
    occurred_at: str
    subject_key: str | None = Field(default=None, max_length=160)
    payload: dict[str, object] = Field(default_factory=dict)

    @field_validator("event_id")
    @classmethod
    def safe_event_id(cls, value: str) -> str:
        if not re.fullmatch(r"[a-zA-Z0-9:_-]+", value):
            raise ValueError("event_id deve ser técnico e não conter dado pessoal")
        return value


class ReplayRequest(BaseModel):
    replay_key: str = Field(min_length=8, max_length=160)
    event_type: str | None = Field(default=None, max_length=80)


class SubjectAnonymizationRequest(BaseModel):
    subject_key: str = Field(min_length=1, max_length=160)
    purpose: str = Field(default="product_impact", min_length=3, max_length=80)


class ModerationReviewRequest(BaseModel):
    decision: Literal["approved", "rejected", "closed"]
    rationale: str = Field(min_length=3, max_length=1000)

    @field_validator("rationale")
    @classmethod
    def clean_rationale(cls, value: str) -> str:
        return value.strip()


class ModerationAppealRequest(BaseModel):
    appeal_key: str = Field(min_length=8, max_length=160)
    appellant_key: str = Field(min_length=1, max_length=160)
    reason: str = Field(min_length=3, max_length=2000)


class ModerationAppealReviewRequest(BaseModel):
    decision: Literal["upheld", "denied"]
    resolution: str = Field(min_length=3, max_length=1000)


class ModelControlRequest(BaseModel):
    enabled: bool
    kill_switch: bool
    canary_percent: int = Field(ge=0, le=100)
    drift_score: float = Field(ge=0, le=1)


class RecommendationRequest(BaseModel):
    decision_key: str = Field(min_length=8, max_length=160)
    subject_key: str | None = Field(default=None, max_length=160)
    candidates: list[str] = Field(min_length=1, max_length=100)


class GeometrySearchRequest(BaseModel):
    decision_key: str = Field(min_length=8, max_length=160)
    entity_type: str = Field(min_length=1, max_length=80)
    features: dict[str, float] = Field(min_length=1, max_length=32)
    limit: int = Field(default=10, ge=1, le=50)
