from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


CaptureStatus = Literal["draft", "review", "ready", "cancelled", "expired"]
HeightBand = Literal["low", "middle", "high"]
ScaleMethod = Literal["none", "known_measurement", "marker"]


class PhotoCaptureCreate(BaseModel):
    project_id: int = Field(gt=0)
    target_photo_count: int = Field(default=24, ge=12, le=80)
    consent_confirmed: bool


class PhotoCaptureScaleUpdate(BaseModel):
    method: ScaleMethod
    value_mm: float | None = Field(default=None, gt=0, le=100_000)
    uncertainty_mm: float | None = Field(default=None, ge=0, le=10_000)

    @model_validator(mode="after")
    def validate_measurement(self):
        if self.method == "none":
            if self.value_mm is not None or self.uncertainty_mm is not None:
                raise ValueError("remova a medida ao continuar sem escala")
        elif self.value_mm is None or self.uncertainty_mm is None:
            raise ValueError("informe a medida e a margem de incerteza")
        return self


class PhotoCapturePhoto(BaseModel):
    id: int
    capture_index: int
    height_band: HeightBand
    file_name: str
    sha256: str
    size_bytes: int
    width: int
    height: int
    quality_status: Literal["accepted", "needs_review"]
    issues: list[str]


class PhotoCaptureSession(BaseModel):
    id: int
    project_id: int
    status: CaptureStatus
    target_photo_count: int
    scale_method: ScaleMethod
    scale_value_mm: float | None
    scale_uncertainty_mm: float | None
    scale_confirmed: bool
    consent_confirmed: bool
    expires_at: str
    created_at: str
    updated_at: str
    photos: list[PhotoCapturePhoto]
    accepted_photo_count: int
    missing_height_bands: list[HeightBand]
    next_actions: list[str]
    can_complete: bool
