from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from types import ModuleType

import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT_DIR / "scripts/reconstruction"


def _load_gateway() -> ModuleType:
    sys.path.insert(0, str(SCRIPT_DIR))
    try:
        spec = importlib.util.spec_from_file_location("tripo_gateway", SCRIPT_DIR / "tripo_gateway.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(str(SCRIPT_DIR))


tripo_gateway = _load_gateway()
tripo_client = sys.modules["tripo_client"]


class FakeClient:
    def __init__(self) -> None:
        self.uploads: list[str] = []
        self.creations = 0

    def upload_image(self, path: Path) -> str:
        self.uploads.append(path.name)
        return f"token-{len(self.uploads)}"

    def create_multiview_task(self, tokens: list[tuple[str, str]], model_version: str) -> str:
        assert len(tokens) == 4
        assert model_version == "v3.1-20260211"
        self.creations += 1
        return "task-123"

    def get_task(self, task_id: str) -> dict[str, object]:
        assert task_id == "task-123"
        return {
            "status": "success",
            "output": {"model": "https://download.example.invalid/model.glb"},
            "consumed_credit": 20,
        }

    def download_model(self, url: str, target: Path) -> None:
        assert url.endswith("model.glb")
        target.write_bytes(b"glTF" + (2).to_bytes(4, "little") + (12).to_bytes(4, "little"))


def _manifest(root: Path, bands: list[str] | None = None) -> Path:
    photos = root / "photos"
    output = root / "output"
    state = root / "state"
    photos.mkdir()
    output.mkdir()
    state.mkdir()
    selected_bands = bands or ["middle"] * 8
    sources = []
    for index, band in enumerate(selected_bands, start=1):
        body = f"photo-{index}".encode()
        name = f"{index:03d}-{band}.jpg"
        (photos / name).write_bytes(body)
        sources.append({
            "file": name,
            "capture_index": index,
            "height_band": band,
            "sha256": hashlib.sha256(body).hexdigest(),
        })
    path = root / "input.json"
    path.write_text(json.dumps({
        "schema": "printora.reconstruction-input/v1",
        "correlation_id": "correlation-123",
        "photos_directory": str(photos),
        "sources": sources,
    }), encoding="utf-8")
    return path


def test_tripo_gateway_reuses_paid_task_and_preserves_unknown_coverage(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    client = FakeClient()
    result_path = tmp_path / "result.json"

    first = tripo_gateway.run_gateway(
        manifest,
        tmp_path / "output",
        result_path,
        client=client,
        state_dir=tmp_path / "state",
        model_version="v3.1-20260211",
        poll_seconds=0.01,
    )
    second = tripo_gateway.run_gateway(
        manifest,
        tmp_path / "output",
        result_path,
        client=client,
        state_dir=tmp_path / "state",
        model_version="v3.1-20260211",
        poll_seconds=0.01,
    )

    assert len(client.uploads) == 4
    assert client.creations == 1
    assert first["observed_ratio"] is None
    assert first["inferred_ratio"] is None
    assert first["provenance"]["selected_capture_indices"] == [1, 3, 6, 8]
    assert first["provenance"]["consumed_credits"] == 20
    assert first["provenance"]["checkpoint_reused"] is False
    assert second["provenance"]["checkpoint_reused"] is True
    assert json.loads(result_path.read_text(encoding="utf-8")) == second


def test_tripo_gateway_requires_four_middle_views(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path, ["middle", "low", "middle", "high", "middle", "low"])

    with pytest.raises(ValueError, match="quatro fotos"):
        tripo_gateway.run_gateway(
            manifest,
            tmp_path / "output",
            tmp_path / "result.json",
            client=FakeClient(),
            state_dir=tmp_path / "state",
            model_version="v3.1-20260211",
        )


def test_tripo_gateway_rejects_checkpoint_for_other_capture(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    client = FakeClient()
    arguments = {
        "client": client,
        "state_dir": tmp_path / "state",
        "model_version": "v3.1-20260211",
        "poll_seconds": 0.01,
    }
    tripo_gateway.run_gateway(manifest, tmp_path / "output", tmp_path / "result.json", **arguments)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    changed = tmp_path / "photos" / payload["sources"][0]["file"]
    changed.write_bytes(b"different-authorized-photo")
    payload["sources"][0]["sha256"] = hashlib.sha256(changed.read_bytes()).hexdigest()
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(RuntimeError, match="checkpoint diverge"):
        tripo_gateway.run_gateway(manifest, tmp_path / "output", tmp_path / "result.json", **arguments)


def test_tripo_client_rejects_private_or_insecure_downloads() -> None:
    with pytest.raises(RuntimeError, match="inválido"):
        tripo_client._require_public_https("http://example.com/model.glb")
    with pytest.raises(RuntimeError, match="privado"):
        tripo_client._require_public_https("https://127.0.0.1/model.glb")


def test_tripo_gateway_rejects_malformed_glb(tmp_path: Path) -> None:
    path = tmp_path / "model.glb"
    path.write_bytes(b"not-a-glb-file")

    with pytest.raises(RuntimeError, match="GLB inválido"):
        tripo_gateway._validate_glb(path)
