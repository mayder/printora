from __future__ import annotations

import hashlib
import json
import os
import signal
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from app.config import Settings
from app.object_storage import ObjectStorage


MAX_RECONSTRUCTION_ARTIFACT_BYTES = 500 * 1024 * 1024
SUPPORTED_MESH_FORMATS = {"obj", "ply", "stl", "glb"}


class ReconstructionUnavailableError(RuntimeError):
    pass


class ReconstructionCancelledError(RuntimeError):
    pass


@dataclass(frozen=True)
class ReconstructionPhotoInput:
    capture_index: int
    height_band: str
    storage_key: str
    sha256: str
    width: int
    height: int


@dataclass(frozen=True)
class ReconstructionAdapterInput:
    job_id: int
    correlation_id: str
    scale_method: str
    scale_value_mm: float | None
    scale_uncertainty_mm: float | None
    photos: tuple[ReconstructionPhotoInput, ...]


@dataclass(frozen=True)
class ReconstructionAdapterResult:
    engine_key: str
    adapter_version: str
    model_version: str
    mesh_format: str
    mesh_bytes: bytes
    unit: str
    observed_ratio: float | None
    inferred_ratio: float | None
    actual_cost_cents: int | None
    parameters: dict[str, object]
    provenance: dict[str, object]


class ReconstructionAdapter(Protocol):
    engine_key: str
    adapter_version: str

    def reconstruct(
        self,
        request: ReconstructionAdapterInput,
        storage: ObjectStorage,
        should_cancel: Callable[[], bool] | None = None,
    ) -> ReconstructionAdapterResult: ...


class DisabledReconstructionAdapter:
    engine_key = "disabled"
    adapter_version = "1"

    def reconstruct(
        self,
        request: ReconstructionAdapterInput,
        storage: ObjectStorage,
        should_cancel: Callable[[], bool] | None = None,
    ) -> ReconstructionAdapterResult:
        raise ReconstructionUnavailableError(
            "A reconstrução ainda não está habilitada neste ambiente. Suas fotos continuam salvas e podem ser retomadas depois."
        )


class FixtureReconstructionAdapter:
    """Adapter determinístico exclusivo para contrato, testes e demonstração local."""

    engine_key = "fixture-photogrammetry"
    adapter_version = "1"

    def reconstruct(
        self,
        request: ReconstructionAdapterInput,
        storage: ObjectStorage,
        should_cancel: Callable[[], bool] | None = None,
    ) -> ReconstructionAdapterResult:
        if should_cancel and should_cancel():
            raise ReconstructionCancelledError("reconstrução cancelada")
        if not request.photos:
            raise ValueError("captura sem fotos")
        mesh = _fixture_obj(request.correlation_id)
        return ReconstructionAdapterResult(
            engine_key=self.engine_key,
            adapter_version=self.adapter_version,
            model_version="synthetic-contract-v1",
            mesh_format="obj",
            mesh_bytes=mesh,
            unit="unknown",
            observed_ratio=None,
            inferred_ratio=None,
            actual_cost_cents=0,
            parameters={"fixture": True},
            provenance={
                "classification": "synthetic_fixture",
                "warning": "Artefato sintético de teste; não representa reconstrução das fotos.",
            },
        )


class CommandReconstructionAdapter:
    adapter_version = "printora-command-v1"

    def __init__(self, *, engine_key: str, executable: Path, timeout_seconds: float) -> None:
        self.engine_key = engine_key
        self.executable = executable.expanduser().resolve()
        self.timeout_seconds = max(30.0, min(timeout_seconds, 14_400.0))

    def reconstruct(
        self,
        request: ReconstructionAdapterInput,
        storage: ObjectStorage,
        should_cancel: Callable[[], bool] | None = None,
    ) -> ReconstructionAdapterResult:
        if not self.executable.is_file():
            raise ReconstructionUnavailableError("O processador 3D configurado não está disponível.")
        with tempfile.TemporaryDirectory(prefix="printora-reconstruction-") as temporary:
            root = Path(temporary).resolve()
            photos_dir = root / "photos"
            output_dir = root / "output"
            photos_dir.mkdir()
            output_dir.mkdir()
            sources: list[dict[str, object]] = []
            for photo in request.photos:
                if should_cancel and should_cancel():
                    raise ReconstructionCancelledError("reconstrução cancelada")
                reader = storage.open_promoted(photo.storage_key)
                suffix = ".jpg" if reader.content_type == "image/jpeg" else ".png"
                target = photos_dir / f"{photo.capture_index:03d}-{photo.height_band}{suffix}"
                try:
                    with target.open("wb") as output:
                        while chunk := reader.body.read(64 * 1024):
                            output.write(chunk)
                finally:
                    reader.body.close()
                if hashlib.sha256(target.read_bytes()).hexdigest() != photo.sha256:
                    raise RuntimeError("checksum de foto divergente antes da reconstrução")
                sources.append({
                    "file": target.name,
                    "capture_index": photo.capture_index,
                    "height_band": photo.height_band,
                    "sha256": photo.sha256,
                    "width": photo.width,
                    "height": photo.height,
                })
            manifest = root / "input.json"
            result_path = root / "result.json"
            manifest.write_text(json.dumps({
                "schema": "printora.reconstruction-input/v1",
                "correlation_id": request.correlation_id,
                "photos_directory": str(photos_dir),
                "sources": sources,
                "scale": {
                    "method": request.scale_method,
                    "value_mm": request.scale_value_mm,
                    "uncertainty_mm": request.scale_uncertainty_mm,
                },
            }, sort_keys=True), encoding="utf-8")
            process = subprocess.Popen(
                [
                    str(self.executable),
                    "--input-manifest", str(manifest),
                    "--output-dir", str(output_dir),
                    "--result", str(result_path),
                ],
                cwd=root,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                env={"PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"},
                text=True,
                start_new_session=True,
            )
            deadline = time.monotonic() + self.timeout_seconds
            while process.poll() is None:
                if should_cancel and should_cancel():
                    _terminate_process(process)
                    raise ReconstructionCancelledError("reconstrução cancelada")
                if time.monotonic() >= deadline:
                    _terminate_process(process)
                    raise RuntimeError("tempo limite do processador 3D excedido")
                time.sleep(0.25)
            if process.returncode != 0:
                raise RuntimeError("o processador 3D não conseguiu reconstruir este objeto")
            return _load_command_result(root, output_dir, result_path, self.engine_key, self.adapter_version)


def _terminate_process(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


def build_reconstruction_adapter(settings: Settings, policy: str) -> ReconstructionAdapter:
    if settings.reconstruction_mode == "fixture":
        return FixtureReconstructionAdapter()
    local = settings.reconstruction_local_command
    provider = settings.reconstruction_provider_command
    if policy == "local" and settings.reconstruction_mode == "local_command" and local:
        return CommandReconstructionAdapter(
            engine_key="local-photogrammetry",
            executable=local,
            timeout_seconds=settings.reconstruction_timeout_seconds,
        )
    if policy == "provider" and settings.reconstruction_mode == "provider_command" and provider:
        return CommandReconstructionAdapter(
            engine_key="provider-multiview-gateway",
            executable=provider,
            timeout_seconds=settings.reconstruction_timeout_seconds,
        )
    if policy == "auto":
        if settings.reconstruction_mode == "local_command" and local:
            return CommandReconstructionAdapter(
                engine_key="local-photogrammetry",
                executable=local,
                timeout_seconds=settings.reconstruction_timeout_seconds,
            )
        if settings.reconstruction_mode == "provider_command" and provider:
            return CommandReconstructionAdapter(
                engine_key="provider-multiview-gateway",
                executable=provider,
                timeout_seconds=settings.reconstruction_timeout_seconds,
            )
    return DisabledReconstructionAdapter()


def _load_command_result(
    root: Path,
    output_dir: Path,
    result_path: Path,
    engine_key: str,
    adapter_version: str,
) -> ReconstructionAdapterResult:
    if not result_path.is_file() or result_path.stat().st_size > 256 * 1024:
        raise RuntimeError("resultado do processador 3D ausente ou inválido")
    payload = json.loads(result_path.read_text(encoding="utf-8"))
    mesh_path = (output_dir / str(payload.get("mesh_file", ""))).resolve()
    if output_dir not in mesh_path.parents or not mesh_path.is_file() or mesh_path.is_symlink():
        raise RuntimeError("artefato do processador 3D inválido")
    mesh_format = str(payload.get("mesh_format", "")).lower()
    if mesh_format not in SUPPORTED_MESH_FORMATS or mesh_path.suffix.lower() != f".{mesh_format}":
        raise RuntimeError("formato de malha do processador 3D não suportado")
    size = mesh_path.stat().st_size
    if size <= 0 or size > MAX_RECONSTRUCTION_ARTIFACT_BYTES:
        raise RuntimeError("malha reconstruída fora do limite seguro")
    observed = _optional_ratio(payload.get("observed_ratio"))
    inferred = _optional_ratio(payload.get("inferred_ratio"))
    return ReconstructionAdapterResult(
        engine_key=str(payload.get("engine_key") or engine_key)[:80],
        adapter_version=adapter_version,
        model_version=str(payload.get("model_version") or "unknown")[:120],
        mesh_format=mesh_format,
        mesh_bytes=mesh_path.read_bytes(),
        unit=str(payload.get("unit") or "unknown")[:20],
        observed_ratio=observed,
        inferred_ratio=inferred,
        actual_cost_cents=_optional_nonnegative_int(payload.get("actual_cost_cents")),
        parameters=dict(payload.get("parameters") or {}),
        provenance=dict(payload.get("provenance") or {}),
    )


def _optional_ratio(value: object) -> float | None:
    if value is None:
        return None
    ratio = float(value)
    if ratio < 0 or ratio > 1:
        raise RuntimeError("proporção de cobertura inválida")
    return ratio


def _optional_nonnegative_int(value: object) -> int | None:
    if value is None:
        return None
    number = int(value)
    if number < 0:
        raise RuntimeError("custo inválido")
    return number


def _fixture_obj(seed: str) -> bytes:
    marker = hashlib.sha256(seed.encode()).hexdigest()[:12]
    return (
        f"# synthetic fixture {marker}\n"
        "v -1 -1 0\nv 1 -1 0\nv 1 1 0\nv -1 1 0\nv 0 0 2\n"
        "f 1 2 5\nf 2 3 5\nf 3 4 5\nf 4 1 5\nf 1 4 3 2\n"
    ).encode()
