from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from app.gcode_cache import normalize_gcode_filename

GcodeManagerAction = Literal[
    "metadata_scan",
    "preheat",
    "directory_create",
    "directory_move",
    "directory_delete",
    "batch_delete",
    "batch_duplicate",
    "batch_move",
    "queue_add",
    "queue_remove",
    "queue_pause",
    "queue_resume",
    "queue_start",
]


class GcodeManagerRequest(BaseModel):
    action: GcodeManagerAction
    filename: str = Field(default="", max_length=512)
    filenames: list[str] = Field(default_factory=list, max_length=50)
    directory: str = Field(default="", max_length=300)
    target_directory: str = Field(default="", max_length=300)
    job_ids: list[str] = Field(default_factory=list, max_length=100)
    confirmation_phrase: str = Field(default="", max_length=1000)
    step_up_token: str | None = Field(default=None, max_length=240)
    hotend_temperature: int = Field(default=0, ge=0, le=300)
    bed_temperature: int = Field(default=0, ge=0, le=130)

    @field_validator("filename")
    @classmethod
    def validate_filename(cls, value: str) -> str:
        return normalize_gcode_filename(value) if value else ""

    @field_validator("filenames")
    @classmethod
    def validate_filenames(cls, values: list[str]) -> list[str]:
        return [normalize_gcode_filename(value) for value in values]

    @field_validator("directory", "target_directory")
    @classmethod
    def validate_directory(cls, value: str) -> str:
        clean = value.replace("\\", "/").strip().strip("/")
        if not clean:
            return ""
        parts = clean.split("/")
        if any(not part or part in {".", ".."} or any(ord(char) < 32 for char in part) for part in parts):
            raise ValueError("pasta G-code inválida")
        return "/".join(parts)


class GcodeManagerResponse(BaseModel):
    printer_id: int
    action: GcodeManagerAction | Literal["queue_status"]
    status: Literal["ready", "blocked", "executed", "failed"]
    summary: str
    blockers: list[str] = Field(default_factory=list)
    job_id: int | None = None
    result: dict[str, Any] = Field(default_factory=dict)


def manager_confirmation_phrase(payload: GcodeManagerRequest) -> str:
    if payload.action == "directory_move":
        return f"MOVER PASTA {payload.directory} -> {payload.target_directory}"
    if payload.action == "directory_delete":
        return f"EXCLUIR PASTA {payload.directory}"
    if payload.action == "batch_delete":
        return f"EXCLUIR {len(payload.filenames)} ARQUIVOS"
    if payload.action == "batch_duplicate":
        return f"DUPLICAR {len(payload.filenames)} ARQUIVOS"
    if payload.action == "batch_move":
        return f"MOVER {len(payload.filenames)} ARQUIVOS -> {payload.target_directory}"
    if payload.action == "queue_add":
        return f"ADICIONAR {len(payload.filenames)} ARQUIVOS NA FILA"
    if payload.action == "queue_remove":
        return f"REMOVER {len(payload.job_ids)} ITENS DA FILA"
    if payload.action == "preheat":
        return f"PRE-AQUECER {payload.hotend_temperature}C / {payload.bed_temperature}C"
    return ""


def manager_requires_step_up(action: GcodeManagerAction) -> bool:
    return action in {"directory_delete", "batch_delete", "batch_move", "preheat"}
