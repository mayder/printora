import hashlib
import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pytest


ROOT_DIR = Path(__file__).resolve().parents[2]


def _load_gateway() -> ModuleType:
    path = ROOT_DIR / "scripts/reconstruction/colmap_gateway.py"
    spec = importlib.util.spec_from_file_location("colmap_gateway", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


colmap_gateway = _load_gateway()


def _manifest(root: Path, count: int = 3) -> Path:
    photos = root / "photos"
    output = root / "output"
    photos.mkdir()
    output.mkdir()
    sources = []
    for index in range(1, count + 1):
        body = f"photo-{index}".encode()
        name = f"{index:03d}-middle.png"
        (photos / name).write_bytes(body)
        sources.append({"file": name, "sha256": hashlib.sha256(body).hexdigest()})
    manifest = root / "input.json"
    manifest.write_text(json.dumps({
        "schema": "printora.reconstruction-input/v1",
        "photos_directory": str(photos),
        "sources": sources,
    }), encoding="utf-8")
    return manifest


def _fake_colmap(path: Path) -> Path:
    path.write_text(
        """#!/bin/sh
set -eu
if [ "$1" = "version" ]; then
  printf 'COLMAP 4.1.1 test without CUDA\\n'
  exit 0
fi
command="$1"
if [ "$command" = "model_analyzer" ]; then
  printf 'Registered images: 3\\nPoints: 42\\nMean reprojection error: 0.25px\\n' >&2
  exit 0
fi
workspace=''
output=''
shift
while [ "$#" -gt 0 ]; do
  case "$1" in
    --workspace_path) workspace="$2"; shift 2 ;;
    --output_path) output="$2"; shift 2 ;;
    *) shift ;;
  esac
done
if [ "$command" = "automatic_reconstructor" ]; then
  mkdir -p "$workspace/sparse/0"
  printf 'model' > "$workspace/sparse/0/cameras.bin"
else
  printf 'ply\\nformat ascii 1.0\\nelement vertex 0\\nend_header\\n' > "$output"
fi
""",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def test_colmap_gateway_generates_versioned_contract_without_false_coverage(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    result_path = tmp_path / "result.json"

    result = colmap_gateway.run_gateway(
        manifest,
        tmp_path / "output",
        result_path,
        colmap_binary=_fake_colmap(tmp_path / "colmap"),
    )

    assert result["mesh_format"] == "ply"
    assert result["engine_key"] == "colmap-photogrammetry"
    assert result["observed_ratio"] is None
    assert result["inferred_ratio"] is None
    assert result["parameters"]["dense"] is False
    assert result["parameters"]["mesher"] == "delaunay_sparse"
    assert result["provenance"]["classification"] == "photogrammetry_unclassified_surface"
    assert result["provenance"]["registered_image_ratio"] == 1
    assert result["provenance"]["mean_reprojection_error_px"] == 0.25
    assert json.loads(result_path.read_text(encoding="utf-8")) == result


def test_colmap_gateway_rejects_source_checksum_mismatch(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["sources"][0]["sha256"] = "0" * 64
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="checksum"):
        colmap_gateway.run_gateway(
            manifest,
            tmp_path / "output",
            tmp_path / "result.json",
            colmap_binary=_fake_colmap(tmp_path / "colmap"),
        )


def test_colmap_gateway_rejects_photo_path_escape(tmp_path: Path) -> None:
    manifest = _manifest(tmp_path)
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    payload["sources"][0]["file"] = "../outside.png"
    manifest.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(ValueError, match="caminho"):
        colmap_gateway.run_gateway(
            manifest,
            tmp_path / "output",
            tmp_path / "result.json",
            colmap_binary=_fake_colmap(tmp_path / "colmap"),
        )
