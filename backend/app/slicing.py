from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.config import Settings
from app.database import connect_database

SlicerEngine = Literal["orcaslicer", "prusaslicer"]
EngineStatus = Literal["ready", "blocked"]
_DEFAULT_ENGINE_ORDER: tuple[SlicerEngine, ...] = ("orcaslicer", "prusaslicer")
_ENGINE_BINARIES: dict[SlicerEngine, tuple[str, ...]] = {
    "orcaslicer": ("orcaslicer", "OrcaSlicer"),
    "prusaslicer": ("prusaslicer", "prusa-slicer", "PrusaSlicer"),
}


class SlicingEngineInfo(BaseModel):
    engine: SlicerEngine
    status: EngineStatus
    configured_path: str | None = None
    detected_path: str | None = None
    version_text: str | None = None
    warnings: list[str] = Field(default_factory=list)
    installation_hint: str
    safe_mode: str = "slicing_engine_detection"


class SlicingRequest(BaseModel):
    model_reference: str = Field(min_length=1, max_length=240)
    printer_reference: str = Field(min_length=1, max_length=160)
    material_reference: str = Field(min_length=1, max_length=120)
    quality_reference: str = Field(min_length=1, max_length=120)
    profile_reference: str | None = Field(default=None, max_length=160)
    engine: SlicerEngine = "orcaslicer"

    @field_validator("model_reference", "printer_reference", "material_reference", "quality_reference", "profile_reference")
    @classmethod
    def reject_sensitive_reference(cls, value: str | None) -> str | None:
        if value is None:
            return None
        compact = value.strip()
        if not compact:
            raise ValueError("referência obrigatória ausente")
        lower = compact.lower()
        if any(marker in lower for marker in ("token", "secret", "password", "passwd", "ssh_key", "ptr_agent_", "ptr_pair_", "ptr_sess_")):
            raise ValueError("referência contém dado sensível")
        return compact


class SlicingDryRunResult(BaseModel):
    status: EngineStatus
    engine: SlicerEngine
    input: SlicingRequest
    command_preview: list[str] = Field(default_factory=list)
    output_contract: dict[str, str]
    warnings: list[str] = Field(default_factory=list)
    sanitized_log: str
    safe_mode: str = "slicing_worker_dry_run"
    rollback_plan: str = "Nenhuma ação necessária: o dry-run não cria G-code nem altera impressora."


class SlicingRepository:
    def __init__(self, database_path: Path):
        self.database_path = database_path

    def record_engine_check(self, info: SlicingEngineInfo) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO slicing_engine_checks (
                    engine, configured_path, detected_path, version_text, status, warnings_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    info.engine,
                    info.configured_path,
                    info.detected_path,
                    info.version_text,
                    info.status,
                    json.dumps(info.warnings, ensure_ascii=False),
                ),
            )

    def record_dry_run(self, result: SlicingDryRunResult) -> None:
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO slicing_dry_run_logs (
                    engine, model_reference, printer_reference, material_reference, quality_reference,
                    status, command_preview_json, warnings_json, sanitized_log
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.engine,
                    result.input.model_reference,
                    result.input.printer_reference,
                    result.input.material_reference,
                    result.input.quality_reference,
                    result.status,
                    json.dumps(result.command_preview, ensure_ascii=False),
                    json.dumps(result.warnings, ensure_ascii=False),
                    result.sanitized_log,
                ),
            )


class SlicingEngineBridge:
    def __init__(self, settings: Settings):
        self.settings = settings

    def detect(self, requested_engine: SlicerEngine | None = None) -> SlicingEngineInfo:
        engine = requested_engine or self._configured_engine()
        configured_path = str(self.settings.slicer_engine_path) if self.settings.slicer_engine_path else None
        detected_path = self._resolve_engine_path(engine)
        warnings: list[str] = []
        version_text: str | None = None
        if detected_path is None:
            warnings.append("Engine de fatiamento não configurada ou não encontrada no PATH.")
            return SlicingEngineInfo(
                engine=engine,
                status="blocked",
                configured_path=_sanitize_text(configured_path),
                detected_path=None,
                version_text=None,
                warnings=warnings,
                installation_hint=_installation_hint(engine),
            )
        version_text = self._read_version(detected_path)
        if version_text is None:
            warnings.append("Engine detectada, mas a versão não pôde ser lida com segurança.")
        return SlicingEngineInfo(
            engine=engine,
            status="ready",
            configured_path=_sanitize_text(configured_path),
            detected_path=_sanitize_text(detected_path),
            version_text=_sanitize_text(version_text),
            warnings=warnings,
            installation_hint=_installation_hint(engine),
        )

    def dry_run(self, payload: SlicingRequest) -> SlicingDryRunResult:
        info = self.detect(payload.engine)
        output_contract = {
            "gcode": "arquivo .gcode gerado em artefato rastreável",
            "logs": "log sanitizado da engine",
            "estimated_time": "tempo estimado informado pela engine quando disponível",
            "estimated_weight": "peso ou filamento estimado quando disponível",
            "warnings": "avisos da engine e validações do Printora",
        }
        warnings = list(info.warnings)
        if info.status != "ready" or info.detected_path is None:
            return SlicingDryRunResult(
                status="blocked",
                engine=payload.engine,
                input=payload,
                output_contract=output_contract,
                warnings=warnings,
                sanitized_log="Dry-run bloqueado: engine de fatiamento indisponível.",
            )
        command_preview = [
            info.detected_path,
            "--export-gcode",
            "--load",
            payload.profile_reference or "<perfil-do-printora>",
            "--printer",
            payload.printer_reference,
            "--filament",
            payload.material_reference,
            "--quality",
            payload.quality_reference,
            "--output",
            "<artefato-printora>/output.gcode",
            payload.model_reference,
        ]
        sanitized_log = _sanitize_text(
            "Dry-run pronto. O Printora executaria a engine em worker isolado, com cwd dedicado, timeout "
            f"{int(self.settings.slicer_engine_timeout_seconds)}s e sem iniciar UI gráfica."
        )
        return SlicingDryRunResult(
            status="ready",
            engine=payload.engine,
            input=payload,
            command_preview=command_preview,
            output_contract=output_contract,
            warnings=warnings,
            sanitized_log=sanitized_log,
        )

    def _configured_engine(self) -> SlicerEngine:
        configured = self.settings.slicer_engine_path
        if configured:
            name = configured.name.lower()
            if "prusa" in name:
                return "prusaslicer"
        return _DEFAULT_ENGINE_ORDER[0]

    def _resolve_engine_path(self, engine: SlicerEngine) -> str | None:
        configured = self.settings.slicer_engine_path
        if configured and configured.is_file() and os.access(configured, os.X_OK):
            return str(configured)
        for binary in _ENGINE_BINARIES[engine]:
            found = shutil.which(binary)
            if found:
                return found
        return None

    def _read_version(self, executable: str) -> str | None:
        try:
            completed = subprocess.run(
                [executable, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=min(self.settings.request_timeout_seconds, 5.0),
            )
        except (OSError, subprocess.SubprocessError):
            return None
        output = (completed.stdout or completed.stderr or "").strip()
        return output.splitlines()[0].strip()[:180] if output else None


def _installation_hint(engine: SlicerEngine) -> str:
    if engine == "prusaslicer":
        return "Instale PrusaSlicer CLI no host/agent e configure PRINTORA_SLICER_ENGINE_PATH quando o binário não estiver no PATH."
    return "Instale OrcaSlicer CLI no host/agent e configure PRINTORA_SLICER_ENGINE_PATH quando o binário não estiver no PATH."


def _sanitize_text(value: str | None) -> str | None:
    if value is None:
        return None
    sanitized = value
    replacements = {
        str(Path.home()): "<home>",
        str(Path("/tmp")): "<tmp>",
    }
    for original, replacement in replacements.items():
        sanitized = sanitized.replace(original, replacement)
    sanitized = re.sub(r"ptr_(agent|pair|sess)_[A-Za-z0-9._-]+", r"ptr_\1_<redacted>", sanitized)
    sanitized = re.sub(r"(?i)(token|password|secret)=\S+", r"\1=<redacted>", sanitized)
    return sanitized
