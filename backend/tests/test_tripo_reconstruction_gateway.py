from __future__ import annotations

import fcntl
import hashlib
import importlib.util
import json
import sys
from datetime import UTC, datetime, timedelta
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


def _load_retention() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "tripo_checkpoint_retention",
        SCRIPT_DIR / "tripo_checkpoint_retention.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


tripo_retention = _load_retention()


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
    checkpoint = next((tmp_path / "state").glob("*.json"))
    checkpoint_payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert checkpoint_payload["schema"] == "printora.tripo-checkpoint/v1"
    assert checkpoint_payload["status"] == "completed"
    assert checkpoint_payload["completed_at"]
    assert checkpoint.stat().st_mode & 0o777 == 0o600


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


def test_tripo_checkpoint_retention_previews_then_removes_only_expired_completed(tmp_path: Path) -> None:
    now = datetime(2026, 8, 2, 12, tzinfo=UTC)
    old_completed = tmp_path / ("a" * 64 + ".json")
    recent_completed = tmp_path / ("b" * 64 + ".json")
    active = tmp_path / ("c" * 64 + ".json")
    legacy = tmp_path / ("d" * 64 + ".json")
    for path, status, completed_at in (
        (old_completed, "completed", now - timedelta(days=31)),
        (recent_completed, "completed", now - timedelta(days=5)),
        (active, "submitted", None),
    ):
        path.write_text(json.dumps({
            "schema": "printora.tripo-checkpoint/v1",
            "status": status,
            "completed_at": completed_at.isoformat() if completed_at else None,
        }), encoding="utf-8")
    legacy.write_text(json.dumps({"task_id": "legacy-task"}), encoding="utf-8")

    preview = tripo_retention.review_checkpoints(tmp_path, retention_days=30, now=now)
    assert preview["mode"] == "preview"
    assert preview["candidates"] == [old_completed.name]
    assert old_completed.exists()

    applied = tripo_retention.review_checkpoints(tmp_path, retention_days=30, apply=True, now=now)

    assert applied["removed_count"] == 1
    assert not old_completed.exists()
    assert recent_completed.exists()
    assert active.exists()
    assert legacy.exists()


def test_tripo_checkpoint_retention_preserves_invalid_symlink_and_locked_checkpoint(tmp_path: Path) -> None:
    now = datetime(2026, 8, 2, 12, tzinfo=UTC)
    completed = {
        "schema": "printora.tripo-checkpoint/v1",
        "status": "completed",
        "completed_at": (now - timedelta(days=90)).isoformat(),
    }
    locked = tmp_path / ("e" * 64 + ".json")
    locked.write_text(json.dumps(completed), encoding="utf-8")
    lock_path = locked.with_suffix(".lock")
    invalid = tmp_path / ("f" * 64 + ".json")
    invalid.write_text("not-json", encoding="utf-8")
    external = tmp_path / "external.json"
    external.write_text(json.dumps(completed), encoding="utf-8")
    symlink = tmp_path / ("1" * 64 + ".json")
    symlink.symlink_to(external)

    with lock_path.open("a+b") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report = tripo_retention.review_checkpoints(
            tmp_path,
            retention_days=30,
            apply=True,
            now=now,
        )

    assert report["candidates"] == [locked.name]
    assert report["removed_count"] == 0
    assert locked.exists()
    assert invalid.exists()
    assert symlink.is_symlink()
    assert external.exists()


def test_tripo_checkpoint_retention_rejects_symlinked_state_directory(tmp_path: Path) -> None:
    state = tmp_path / "state"
    state.mkdir()
    linked_state = tmp_path / "linked-state"
    linked_state.symlink_to(state, target_is_directory=True)

    with pytest.raises(ValueError, match="diretório de checkpoint inválido"):
        tripo_retention.review_checkpoints(linked_state)
