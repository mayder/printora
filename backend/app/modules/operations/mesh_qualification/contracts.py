from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field, model_validator


RepairOperation = Literal["clean", "orient_normals", "close_holes", "remove_small_components", "decimate", "convert"]


class MeshRepairCreate(BaseModel):
    operation: RepairOperation
    source_revision_id: int | None = Field(default=None, gt=0)
    parameters: dict[str, object] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_parameters(self) -> "MeshRepairCreate":
        allowed = {
            "clean": {"weld_tolerance", "output_format"},
            "orient_normals": {"output_format"},
            "close_holes": {"maximum_hole_edges", "output_format"},
            "remove_small_components": {"minimum_triangles", "output_format"},
            "decimate": {"target_ratio", "output_format"},
            "convert": {"output_format"},
        }[self.operation]
        if set(self.parameters) - allowed:
            raise ValueError("A correção contém opções não reconhecidas.")
        if len(json.dumps(self.parameters, ensure_ascii=False).encode()) > 2_048:
            raise ValueError("As opções da correção excedem o limite permitido.")
        return self


class MeshRevision(BaseModel):
    id: int
    reconstruction_job_id: int
    source_artifact_id: int
    parent_revision_id: int | None
    operation: RepairOperation
    parameters: dict[str, object]
    status: Literal["queued", "processing", "succeeded", "failed", "cancelled"]
    output_format: str | None
    sha256: str | None
    size_bytes: int | None
    unit: str
    manifest: dict[str, object]
    qualification: dict[str, object]
    error_message: str | None
    can_cancel: bool
    next_action: str
    created_at: str
    updated_at: str
