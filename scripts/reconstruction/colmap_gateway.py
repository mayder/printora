#!/usr/bin/env python3
"""Gateway local COLMAP para o contrato de reconstrução do Printora."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Sequence


COLMAP_CANDIDATES = (
    Path("/usr/local/bin/colmap"),
    Path("/opt/homebrew/bin/colmap"),
    Path("/usr/bin/colmap"),
)
MAX_MANIFEST_BYTES = 256 * 1024
MAX_MESH_BYTES = 500 * 1024 * 1024
MAX_PHOTOS = 80


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        run_gateway(args.input_manifest, args.output_dir, args.result)
    except Exception as exc:
        print(f"COLMAP gateway failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    return 0


def run_gateway(
    manifest_path: Path,
    output_dir: Path,
    result_path: Path,
    *,
    colmap_binary: Path | None = None,
) -> dict[str, object]:
    manifest_path = manifest_path.resolve()
    output_dir = output_dir.resolve()
    result_path = result_path.resolve()
    root = manifest_path.parent
    _require_inside(output_dir, root)
    _require_inside(result_path, root)
    payload = _load_manifest(manifest_path)
    photos_dir = Path(str(payload["photos_directory"])).resolve()
    _require_inside(photos_dir, root)
    sources = _validate_sources(payload.get("sources"), photos_dir)
    binary = (colmap_binary or _find_colmap()).resolve()
    if not binary.is_file():
        raise RuntimeError("COLMAP não encontrado")

    version = _colmap_version(binary)
    dense = "without CUDA" not in version
    workspace = output_dir / "colmap-workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    _run_colmap(binary, workspace, photos_dir, dense=dense)
    if not dense:
        _mesh_sparse_models(binary, workspace)
    mesh = _select_mesh(workspace, dense=dense)
    sparse_metrics = _analyze_sparse_models(binary, workspace, len(sources))
    final_mesh = output_dir / "raw-photogrammetry.ply"
    shutil.copyfile(mesh, final_mesh)
    elapsed = round(time.monotonic() - started, 3)
    result: dict[str, object] = {
        "mesh_file": final_mesh.name,
        "mesh_format": "ply",
        "engine_key": "colmap-photogrammetry",
        "model_version": version,
        "unit": "unknown",
        "observed_ratio": None,
        "inferred_ratio": None,
        "actual_cost_cents": 0,
        "parameters": {
            "quality": "medium",
            "dense": dense,
            "mesher": "poisson" if dense else "delaunay_sparse",
            "gpu": False,
            "single_camera": True,
        },
        "provenance": {
            "classification": "photogrammetry_unclassified_surface",
            "source_count": len(sources),
            "elapsed_seconds": elapsed,
            **sparse_metrics,
            "warning": (
                "A superfície esparsa de compatibilidade precisa de qualificação antes do uso."
                if not dense
                else "A superfície não possui classificação por região observada ou inferida."
            ),
        },
    }
    result_path.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    return result


def _load_manifest(path: Path) -> dict[str, object]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_MANIFEST_BYTES:
        raise ValueError("manifesto inválido")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != "printora.reconstruction-input/v1":
        raise ValueError("contrato de manifesto incompatível")
    return payload


def _validate_sources(raw_sources: object, photos_dir: Path) -> list[dict[str, object]]:
    if not isinstance(raw_sources, list) or not 3 <= len(raw_sources) <= MAX_PHOTOS:
        raise ValueError("quantidade de fotos inválida")
    sources: list[dict[str, object]] = []
    for source in raw_sources:
        if not isinstance(source, dict):
            raise ValueError("fonte inválida")
        name = str(source.get("file", ""))
        photo = (photos_dir / name).resolve()
        if Path(name).name != name or photos_dir not in photo.parents or not photo.is_file() or photo.is_symlink():
            raise ValueError("caminho de foto inválido")
        expected = str(source.get("sha256", ""))
        if len(expected) != 64 or _sha256(photo) != expected:
            raise ValueError("checksum de foto divergente")
        sources.append(source)
    return sources


def _find_colmap() -> Path:
    discovered = shutil.which("colmap")
    candidates = ((Path(discovered),) if discovered else ()) + COLMAP_CANDIDATES
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise RuntimeError("COLMAP não encontrado")


def _run_colmap(binary: Path, workspace: Path, photos_dir: Path, *, dense: bool) -> None:
    subprocess.run(
        [
            str(binary),
            "automatic_reconstructor",
            "--workspace_path", str(workspace),
            "--image_path", str(photos_dir),
            "--data_type", "individual",
            "--quality", "medium",
            "--camera_model", "SIMPLE_RADIAL",
            "--single_camera", "1",
            "--dense", "1" if dense else "0",
            "--mesher", "poisson",
            "--use_gpu", "0",
            "--log_target", "stderr",
            "--log_color", "0",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
        env={"PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"},
    )


def _mesh_sparse_models(binary: Path, workspace: Path) -> None:
    models = sorted(path for path in (workspace / "sparse").glob("*") if path.is_dir() and not path.is_symlink())
    if not models:
        raise RuntimeError("COLMAP não registrou câmeras suficientes")
    output = workspace / "sparse-mesh"
    output.mkdir()
    for model in models:
        subprocess.run(
            [
                str(binary),
                "delaunay_mesher",
                "--input_path", str(model),
                "--input_type", "sparse",
                "--output_path", str(output / f"{model.name}.ply"),
                "--log_target", "stderr",
                "--log_color", "0",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
            env={"PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"},
        )


def _select_mesh(workspace: Path, *, dense: bool) -> Path:
    pattern = "dense/*/meshed-poisson.ply" if dense else "sparse-mesh/*.ply"
    meshes = [
        path for path in workspace.glob(pattern)
        if path.is_file() and not path.is_symlink() and 0 < path.stat().st_size <= MAX_MESH_BYTES
    ]
    if not meshes:
        raise RuntimeError("COLMAP não produziu superfície densa")
    return max(meshes, key=lambda path: path.stat().st_size)


def _analyze_sparse_models(binary: Path, workspace: Path, source_count: int) -> dict[str, object]:
    candidates: list[dict[str, object]] = []
    for model in sorted(path for path in (workspace / "sparse").glob("*") if path.is_dir()):
        completed = subprocess.run(
            [str(binary), "model_analyzer", "--path", str(model), "--log_color", "0"],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
            env={"PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"},
        )
        output = f"{completed.stdout}\n{completed.stderr}"
        registered = _metric_int(output, "Registered images")
        candidates.append({
            "registered_images": registered,
            "registered_image_ratio": round(registered / source_count, 6),
            "sparse_points": _metric_int(output, "Points"),
            "mean_reprojection_error_px": _metric_float(output, "Mean reprojection error"),
        })
    if not candidates:
        raise RuntimeError("COLMAP não produziu modelo esparso analisável")
    return max(candidates, key=lambda item: int(item["registered_images"]))


def _metric_int(output: str, label: str) -> int:
    match = re.search(rf"{re.escape(label)}:\s+(\d+)", output)
    if match is None:
        raise RuntimeError(f"métrica ausente: {label}")
    return int(match.group(1))


def _metric_float(output: str, label: str) -> float:
    match = re.search(rf"{re.escape(label)}:\s+([0-9.]+)", output)
    if match is None:
        raise RuntimeError(f"métrica ausente: {label}")
    return float(match.group(1))


def _colmap_version(binary: Path) -> str:
    completed = subprocess.run(
        [str(binary), "version"],
        capture_output=True,
        text=True,
        timeout=10,
        check=True,
        env={"PATH": "/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin"},
    )
    line = (completed.stdout or completed.stderr).splitlines()[0]
    return line.strip()[:120]


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
