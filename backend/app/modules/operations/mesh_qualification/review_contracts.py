from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


class MeshReviewCreate(BaseModel):
    decision: Literal["approve", "reject"]
    intended_use: Literal["decorative", "prototype", "mechanical"] = "decorative"
    known_axis: Literal["x", "y", "z"] | None = None
    known_dimension_mm: float | None = Field(default=None, gt=0, le=2_000)
    shape_reviewed: bool = False
    limitations_accepted: bool = False
    note: str = Field(default="", max_length=500)

    @model_validator(mode="after")
    def validate_review(self) -> "MeshReviewCreate":
        if self.decision == "approve":
            if not self.shape_reviewed or not self.limitations_accepted:
                raise ValueError("Confirme a forma e as limitações antes de continuar.")
            if self.known_axis is None or self.known_dimension_mm is None:
                raise ValueError("Confira uma medida real do objeto antes de continuar.")
        return self


class MeshRevisionReview(BaseModel):
    id: int
    revision_id: int
    reconstruction_job_id: int
    decision: Literal["approved_for_slicing", "rejected"]
    intended_use: Literal["decorative", "prototype", "mechanical"]
    known_axis: str | None
    known_dimension_mm: float | None
    model_dimension_mm: float | None
    deviation_percent: float | None
    revision_sha256: str
    review_manifest: dict[str, object]
    qualification: dict[str, object]
    project_file_id: int | None
    note: str
    created_at: str
