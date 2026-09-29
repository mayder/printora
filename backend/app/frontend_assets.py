from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path, PurePosixPath

ALLOWED_FRONTEND_ASSET_EXTENSIONS = frozenset(
    {
        ".css",
        ".gif",
        ".ico",
        ".jpeg",
        ".jpg",
        ".js",
        ".json",
        ".map",
        ".png",
        ".svg",
        ".ttf",
        ".wasm",
        ".webp",
        ".woff",
        ".woff2",
    }
)


def resolve_frontend_asset_path(asset_path: str, frontend_dist_dir: Path) -> Path | None:
    relative_path = _safe_relative_asset_path(asset_path)
    if relative_path is None:
        return None

    current_asset = frontend_dist_dir / "assets" / relative_path
    if current_asset.is_file():
        return current_asset

    for release_dir in _frontend_release_dirs(frontend_dist_dir):
        release_asset = release_dir / "frontend" / "dist" / "assets" / relative_path
        if release_asset.is_file():
            return release_asset
    return None


def _safe_relative_asset_path(asset_path: str) -> Path | None:
    if not asset_path or asset_path.startswith("/"):
        return None

    posix_path = PurePosixPath(asset_path)
    if any(part in {"", ".", ".."} for part in posix_path.parts):
        return None
    if posix_path.suffix.lower() not in ALLOWED_FRONTEND_ASSET_EXTENSIONS:
        return None
    return Path(*posix_path.parts)


def _frontend_release_dirs(frontend_dist_dir: Path) -> Iterator[Path]:
    deployment_base = _deployment_base_path(frontend_dist_dir)
    if deployment_base is None:
        return

    releases_dir = deployment_base / "releases"
    if not releases_dir.is_dir():
        return

    def release_mtime(path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    release_dirs = [path for path in releases_dir.iterdir() if path.is_dir()]
    yield from sorted(release_dirs, key=release_mtime, reverse=True)


def _deployment_base_path(frontend_dist_dir: Path) -> Path | None:
    try:
        release_link = frontend_dist_dir.parents[1]
    except IndexError:
        return None

    if release_link.name == "current":
        return release_link.parent

    try:
        slots_dir = frontend_dist_dir.parents[2]
    except IndexError:
        return None

    if slots_dir.name == "slots":
        return slots_dir.parent
    return None
