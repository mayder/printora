#!/usr/bin/env python3
"""Gateway multiview Tripo para o contrato de reconstrução do Printora."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol, Sequence

from tripo_client import FINAL_STATUSES, TripoClient


MAX_MANIFEST_BYTES = 256 * 1024
MAX_PHOTOS = 80
CHECKPOINT_SCHEMA = "printora.tripo-checkpoint/v1"
SUPPORTED_MODELS = {"v3.1-20260211", "v3.0-20250812", "v2.5-20250123", "P1-20260311"}


class ProviderClient(Protocol):
    def upload_image(self, path: Path) -> str: ...
    def create_multiview_task(self, tokens: list[tuple[str, str]], model_version: str) -> str: ...
    def get_task(self, task_id: str) -> dict[str, object]: ...
    def download_model(self, url: str, target: Path) -> None: ...


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        key = os.environ.get("PRINTORA_TRIPO_API_KEY", "")
        state_dir_raw = os.environ.get("PRINTORA_TRIPO_STATE_DIR", "")
        if not state_dir_raw:
            raise RuntimeError("diretório de checkpoint do provedor não configurado")
        run_gateway(
            args.input_manifest,
            args.output_dir,
            args.result,
            client=TripoClient(key),
            state_dir=Path(state_dir_raw),
            model_version=os.environ.get("PRINTORA_TRIPO_MODEL_VERSION", "v3.1-20260211"),
        )
    except Exception as exc:
        print(f"Tripo gateway failed: {type(exc).__name__}", file=os.sys.stderr)
        return 1
    return 0


def run_gateway(
    manifest_path: Path,
    output_dir: Path,
    result_path: Path,
    *,
    client: ProviderClient,
    state_dir: Path,
    model_version: str,
    poll_seconds: float = 5.0,
    timeout_seconds: float = 3300.0,
) -> dict[str, object]:
    if model_version not in SUPPORTED_MODELS:
        raise ValueError("versão de modelo não homologada")
    manifest_path = manifest_path.resolve()
    root = manifest_path.parent
    output_dir = output_dir.resolve()
    result_path = result_path.resolve()
    _require_inside(output_dir, root)
    _require_inside(result_path, root)
    payload = _load_manifest(manifest_path)
    correlation_id = str(payload.get("correlation_id", ""))
    if not correlation_id or len(correlation_id) > 160:
        raise ValueError("correlação ausente")
    photos_dir = Path(str(payload["photos_directory"])).resolve()
    _require_inside(photos_dir, root)
    sources = _validate_sources(payload.get("sources"), photos_dir)
    selected = _select_middle_views(sources)
    fingerprint = _fingerprint(selected, model_version)
    state_dir_input = state_dir.expanduser()
    if not state_dir_input.is_absolute() or not state_dir_input.is_dir() or state_dir_input.is_symlink():
        raise ValueError("diretório de checkpoint inválido")
    state_dir = state_dir_input.resolve()
    checkpoint = state_dir / f"{hashlib.sha256(correlation_id.encode()).hexdigest()}.json"
    lock_path = checkpoint.with_suffix(".lock")
    started = time.monotonic()
    with lock_path.open("a+b") as lock:
        os.chmod(lock_path, 0o600)
        fcntl.flock(lock, fcntl.LOCK_EX)
        task_id = _read_checkpoint(checkpoint, fingerprint)
        reused = task_id is not None
        if task_id is None:
            tokens = [
                (_file_type(item["path"]), client.upload_image(item["path"]))
                for item in selected
            ]
            task_id = client.create_multiview_task(tokens, model_version)
            _write_checkpoint(checkpoint, fingerprint, task_id)
        task = _wait_for_task(client, task_id, poll_seconds, timeout_seconds)
        output = task.get("output")
        if not isinstance(output, dict) or not isinstance(output.get("model"), str):
            raise RuntimeError("provedor concluiu sem modelo")
        output_dir.mkdir(parents=True, exist_ok=True)
        mesh = output_dir / "raw-provider.glb"
        client.download_model(str(output["model"]), mesh)
        _validate_glb(mesh)
        consumed = task.get("consumed_credit")
        consumed_credits = int(consumed) if consumed is not None else None
        if consumed_credits is not None and consumed_credits < 0:
            raise RuntimeError("custo do provedor inválido")
        result: dict[str, object] = {
            "mesh_file": mesh.name,
            "mesh_format": "glb",
            "engine_key": "tripo-multiview",
            "model_version": model_version,
            "unit": "unknown",
            "observed_ratio": None,
            "inferred_ratio": None,
            "actual_cost_cents": None,
            "parameters": {
                "texture": False,
                "pbr": False,
                "view_order": ["front", "left", "back", "right"],
            },
            "provenance": {
                "classification": "provider_generated_unclassified_surface",
                "source_count": 4,
                "selected_capture_indices": [int(item["capture_index"]) for item in selected],
                "provider_task_id": task_id,
                "checkpoint_reused": reused,
                "consumed_credits": consumed_credits,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "warning": "A superfície não distingue regiões observadas de regiões inferidas.",
            },
        }
        result_path.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        _mark_checkpoint_completed(checkpoint, fingerprint, task_id)
        return result


def _wait_for_task(
    client: ProviderClient,
    task_id: str,
    poll_seconds: float,
    timeout_seconds: float,
) -> dict[str, object]:
    deadline = time.monotonic() + max(30.0, timeout_seconds)
    while True:
        task = client.get_task(task_id)
        status = str(task.get("status", ""))
        if status == "success":
            return task
        if status in FINAL_STATUSES:
            raise RuntimeError(f"tarefa do provedor terminou sem sucesso: {status}")
        if status not in {"queued", "running"}:
            raise RuntimeError("estado incompatível do provedor")
        if time.monotonic() >= deadline:
            raise RuntimeError("tempo limite do provedor excedido")
        time.sleep(max(0.05, poll_seconds))


def _load_manifest(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError("manifesto inválido")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "printora.reconstruction-input/v1":
        raise ValueError("contrato de manifesto incompatível")
    return payload


def _validate_sources(raw: object, photos_dir: Path) -> list[dict[str, object]]:
    if not isinstance(raw, list) or not 4 <= len(raw) <= MAX_PHOTOS:
        raise ValueError("quantidade de fotos inválida")
    sources: list[dict[str, object]] = []
    for source in raw:
        if not isinstance(source, dict):
            raise ValueError("fonte inválida")
        name = str(source.get("file", ""))
        path = (photos_dir / name).resolve()
        if Path(name).name != name or photos_dir not in path.parents or not path.is_file() or path.is_symlink():
            raise ValueError("caminho de foto inválido")
        if str(source.get("height_band")) not in {"low", "middle", "high"}:
            raise ValueError("altura da foto inválida")
        expected = str(source.get("sha256", ""))
        if len(expected) != 64 or _sha256(path) != expected:
            raise ValueError("checksum de foto divergente")
        sources.append({**source, "path": path})
    return sources


def _select_middle_views(sources: list[dict[str, object]]) -> list[dict[str, object]]:
    middle = sorted(
        (source for source in sources if source["height_band"] == "middle"),
        key=lambda source: int(source["capture_index"]),
    )
    if len(middle) < 4:
        raise ValueError("são necessárias quatro fotos na altura do objeto")
    indexes = [round(position * (len(middle) - 1) / 3) for position in range(4)]
    return [middle[index] for index in indexes]


def _read_checkpoint(path: Path, fingerprint: str) -> str | None:
    if not path.exists():
        return None
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 16 * 1024:
        raise RuntimeError("checkpoint do provedor inválido")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("fingerprint") != fingerprint:
        raise RuntimeError("checkpoint diverge da captura")
    task_id = str(payload.get("task_id", ""))
    if not task_id or len(task_id) > 160:
        raise RuntimeError("checkpoint sem tarefa válida")
    return task_id


def _write_checkpoint(path: Path, fingerprint: str, task_id: str) -> None:
    now = _utc_now()
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps({
        "schema": CHECKPOINT_SCHEMA,
        "fingerprint": fingerprint,
        "task_id": task_id,
        "status": "submitted",
        "created_at": now,
        "updated_at": now,
        "completed_at": None,
    }, sort_keys=True), encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def _mark_checkpoint_completed(path: Path, fingerprint: str, task_id: str) -> None:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("fingerprint") != fingerprint or payload.get("task_id") != task_id:
        raise RuntimeError("checkpoint divergiu durante a conclusão")
    now = _utc_now()
    payload.update({
        "schema": CHECKPOINT_SCHEMA,
        "status": "completed",
        "updated_at": now,
        "completed_at": now,
    })
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    os.chmod(temporary, 0o600)
    temporary.replace(path)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat()


def _fingerprint(selected: list[dict[str, object]], model_version: str) -> str:
    value = model_version + "\n" + "\n".join(str(item["sha256"]) for item in selected)
    return hashlib.sha256(value.encode()).hexdigest()


def _file_type(path: Path) -> str:
    return "jpeg" if path.suffix.lower() in {".jpg", ".jpeg"} else "png"


def _validate_glb(path: Path) -> None:
    size = path.stat().st_size
    if size < 12:
        raise RuntimeError("modelo GLB inválido")
    header = path.read_bytes()[:12]
    version = int.from_bytes(header[4:8], "little")
    declared_size = int.from_bytes(header[8:12], "little")
    if header[:4] != b"glTF" or version != 2 or declared_size != size:
        raise RuntimeError("modelo GLB inválido")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        while chunk := source.read(64 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _require_inside(path: Path, root: Path) -> None:
    if path == root or root not in path.parents:
        raise ValueError("caminho fora do diretório temporário")


if __name__ == "__main__":
    raise SystemExit(main())
