from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


MaterialSource = Literal["local", "spoolman"]
StorageState = Literal["unknown", "sealed", "open", "drying", "dry"]
ConsumptionStatus = Literal["planned", "confirmed", "released"]
CompatibilityStatus = Literal["compatible", "incompatible", "unknown"]


class SpoolPayload(BaseModel):
    material_profile_id: int | None = Field(default=None, ge=1)
    name: str = Field(min_length=2, max_length=120)
    material_type: str = Field(min_length=2, max_length=40)
    brand: str = Field(default="", max_length=80)
    color_name: str = Field(default="", max_length=80)
    color_hex: str | None = Field(default=None, max_length=7)
    lot_code: str = Field(default="", max_length=100)
    initial_weight_g: float | None = Field(default=None, ge=0, le=100_000)
    remaining_weight_g: float | None = Field(default=None, ge=0, le=100_000)
    location: str = Field(default="", max_length=160)
    storage_state: StorageState = "unknown"
    opened_at: str | None = Field(default=None, max_length=40)
    dried_at: str | None = Field(default=None, max_length=40)
    expires_at: str | None = Field(default=None, max_length=40)

    @field_validator("name", "material_type", "brand", "color_name", "lot_code", "location")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @field_validator("color_hex")
    @classmethod
    def clean_color(cls, value: str | None) -> str | None:
        if value is None or not value.strip():
            return None
        cleaned = value.strip().upper()
        if not re.fullmatch(r"#[0-9A-F]{6}", cleaned):
            raise ValueError("cor hexadecimal deve usar o formato #RRGGBB")
        return cleaned

    @model_validator(mode="after")
    def validate_weights(self) -> "SpoolPayload":
        if (
            self.initial_weight_g is not None
            and self.remaining_weight_g is not None
            and self.remaining_weight_g > self.initial_weight_g
        ):
            raise ValueError("peso disponível não pode superar o peso inicial")
        return self


class SpoolUpdatePayload(SpoolPayload):
    revision: int = Field(ge=1)


class MaterialAlert(BaseModel):
    code: str
    severity: Literal["info", "warning"]
    title: str
    detail: str
    action: str


class MaterialSpool(BaseModel):
    id: int
    owner_user_id: int
    material_profile_id: int | None
    source: MaterialSource
    external_id: str | None
    name: str
    material_type: str
    brand: str
    color_name: str
    color_hex: str | None
    lot_code: str
    initial_weight_g: float | None
    remaining_weight_g: float | None
    location: str
    storage_state: StorageState
    opened_at: str | None
    dried_at: str | None
    expires_at: str | None
    revision: int
    status: Literal["active", "archived"]
    last_synced_at: str | None
    created_at: str
    updated_at: str
    alerts: list[MaterialAlert] = Field(default_factory=list)


class ConsumptionPayload(BaseModel):
    spool_id: int = Field(ge=1)
    slicing_job_id: int | None = Field(default=None, ge=1)
    print_history_id: int | None = Field(default=None, ge=1)
    idempotency_key: str = Field(min_length=8, max_length=160)
    predicted_weight_g: float | None = Field(default=None, ge=0, le=100_000)
    actual_weight_g: float | None = Field(default=None, ge=0, le=100_000)
    status: ConsumptionStatus
    note: str = Field(default="", max_length=1000)

    @field_validator("idempotency_key", "note")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.strip().split())

    @model_validator(mode="after")
    def validate_amount(self) -> "ConsumptionPayload":
        if self.status == "confirmed" and self.actual_weight_g is None:
            raise ValueError("consumo confirmado exige peso realizado")
        if self.status == "planned" and self.predicted_weight_g is None:
            raise ValueError("planejamento exige peso previsto")
        return self


class MaterialConsumption(BaseModel):
    id: int
    owner_user_id: int
    spool_id: int
    slicing_job_id: int | None
    print_history_id: int | None
    idempotency_key: str
    predicted_weight_g: float | None
    actual_weight_g: float | None
    status: ConsumptionStatus
    remaining_weight_after_g: float | None
    note: str
    created_at: str
    confirmed_at: str | None
    released_at: str | None


class QualitySamplePayload(BaseModel):
    spool_id: int = Field(ge=1)
    print_history_id: int | None = Field(default=None, ge=1)
    sample_type: Literal["dimensional", "calibration"]
    metric_name: str = Field(min_length=2, max_length=120)
    nominal_value_mm: float = Field(ge=0, le=100_000)
    measured_value_mm: float = Field(ge=0, le=100_000)
    tolerance_mm: float = Field(ge=0, le=10_000)
    photo_object_id: int | None = Field(default=None, ge=1)
    note: str = Field(default="", max_length=1000)

    @field_validator("metric_name", "note")
    @classmethod
    def clean_text(cls, value: str) -> str:
        return " ".join(value.strip().split())


class MaterialQualitySample(BaseModel):
    id: int
    owner_user_id: int
    spool_id: int
    print_history_id: int | None
    sample_type: Literal["dimensional", "calibration"]
    metric_name: str
    nominal_value_mm: float
    measured_value_mm: float
    tolerance_mm: float
    deviation_mm: float
    result: Literal["passed", "failed"]
    photo_object_id: int | None
    note: str
    created_at: str


class CompatibilityRequest(BaseModel):
    spool_id: int = Field(ge=1)
    printer_id: int = Field(ge=1)
    material_profile_id: int | None = Field(default=None, ge=1)
    required_weight_g: float | None = Field(default=None, ge=0, le=100_000)
    ventilation_confirmed: bool | None = None


class CompatibilityResult(BaseModel):
    status: CompatibilityStatus
    reasons: list[str]
    warnings: list[str]
    available_weight_g: float | None
    required_weight_g: float | None


class SpoolmanSyncResult(BaseModel):
    printer_id: int
    status: Literal["synced", "unavailable"]
    imported: int = 0
    updated: int = 0
    total: int = 0
    detail: str
