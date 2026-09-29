from __future__ import annotations

from pathlib import Path

from app.frontend_assets import resolve_frontend_asset_path


def test_frontend_asset_resolves_current_build_first(tmp_path: Path) -> None:
    dist_dir = tmp_path / "current" / "frontend" / "dist"
    current_asset = dist_dir / "assets" / "index-current.js"
    current_asset.parent.mkdir(parents=True)
    current_asset.write_text("current", encoding="utf-8")

    assert resolve_frontend_asset_path("index-current.js", dist_dir) == current_asset


def test_frontend_asset_falls_back_to_previous_release_for_open_tabs(tmp_path: Path) -> None:
    dist_dir = tmp_path / "current" / "frontend" / "dist"
    dist_dir.mkdir(parents=True)
    old_asset = tmp_path / "releases" / "sha-old" / "frontend" / "dist" / "assets" / "sindarius-gcodeviewer.es-old.js"
    old_asset.parent.mkdir(parents=True)
    old_asset.write_text("old gcode viewer", encoding="utf-8")

    assert resolve_frontend_asset_path("sindarius-gcodeviewer.es-old.js", dist_dir) == old_asset


def test_frontend_asset_falls_back_from_blue_green_slot_path(tmp_path: Path) -> None:
    dist_dir = tmp_path / "slots" / "blue" / "frontend" / "dist"
    dist_dir.mkdir(parents=True)
    old_asset = tmp_path / "releases" / "sha-old" / "frontend" / "dist" / "assets" / "chunk-old.css"
    old_asset.parent.mkdir(parents=True)
    old_asset.write_text("old css", encoding="utf-8")

    assert resolve_frontend_asset_path("chunk-old.css", dist_dir) == old_asset


def test_frontend_asset_rejects_traversal_and_unknown_extensions(tmp_path: Path) -> None:
    dist_dir = tmp_path / "current" / "frontend" / "dist"

    assert resolve_frontend_asset_path("../secret.js", dist_dir) is None
    assert resolve_frontend_asset_path("/absolute.js", dist_dir) is None
    assert resolve_frontend_asset_path("asset.py", dist_dir) is None
