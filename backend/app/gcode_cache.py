from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from starlette.background import BackgroundTask

from app.agent_pairing import AgentRecord
from app.config import Settings

MAX_GCODE_CACHE_BYTES = 96 * 1024 * 1024
GCODE_CACHE_TTL_SECONDS = 48 * 60 * 60

_CACHE_KEY_RE = re.compile(r"^[a-f0-9]{32,64}$")
_ALLOWED_GCODE_EXTENSIONS = {".g", ".gc", ".gco", ".gcode", ".nc", ".ngc", ".tap"}


class GcodeCachePrepareRequest(BaseModel):
    filename: str = Field(min_length=1, max_length=512)


class GcodeCacheEntry(BaseModel):
    status: Literal["cached"] = "cached"
    cache_key: str
    printer_id: int
    filename: str
    size_bytes: int
    sha256: str
    created_at: str


class GcodeUploadEntry(BaseModel):
    status: Literal["staged"] = "staged"
    upload_key: str
    printer_id: int
    filename: str
    size_bytes: int
    sha256: str
    created_at: str


def normalize_gcode_filename(filename: str) -> str:
    value = filename.replace("\\", "/").strip()
    if not value or value.startswith("/") or "\x00" in value:
        raise HTTPException(status_code=400, detail="nome de G-code inválido")
    parts = [part for part in value.split("/") if part]
    if not parts or any(part in {".", ".."} for part in parts):
        raise HTTPException(status_code=400, detail="nome de G-code inválido")
    if any(any(ord(char) < 32 for char in part) for part in parts):
        raise HTTPException(status_code=400, detail="nome de G-code inválido")
    normalized = "/".join(parts)
    extension = Path(normalized).suffix.lower()
    if extension not in _ALLOWED_GCODE_EXTENSIONS:
        raise HTTPException(status_code=400, detail="arquivo não parece ser G-code")
    return normalized


def gcode_cache_key(printer_id: int, filename: str) -> str:
    normalized = normalize_gcode_filename(filename)
    return hashlib.sha256(f"{printer_id}\0{normalized}".encode("utf-8")).hexdigest()


def read_gcode_cache_entry(settings: Settings, printer_id: int, cache_key: str) -> GcodeCacheEntry | None:
    cache_key = validate_gcode_cache_key(cache_key)
    entry_path = _entry_path(settings, printer_id, cache_key)
    data_path = _data_path(settings, printer_id, cache_key)
    if not entry_path.exists() or not data_path.exists():
        return None
    if _is_stale(entry_path):
        _remove_cache_files(entry_path, data_path)
        return None
    try:
        entry = GcodeCacheEntry.model_validate(json.loads(entry_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError):
        _remove_cache_files(entry_path, data_path)
        return None
    if entry.printer_id != printer_id or entry.cache_key != cache_key:
        _remove_cache_files(entry_path, data_path)
        return None
    if data_path.stat().st_size != entry.size_bytes:
        _remove_cache_files(entry_path, data_path)
        return None
    return entry


def gcode_cache_file_response(settings: Settings, printer_id: int, cache_key: str) -> FileResponse:
    entry = read_gcode_cache_entry(settings, printer_id, cache_key)
    if entry is None:
        raise HTTPException(status_code=404, detail="G-code não está em cache")
    return FileResponse(
        _data_path(settings, printer_id, entry.cache_key),
        media_type="text/plain; charset=utf-8",
        filename=Path(entry.filename).name,
    )


async def store_gcode_cache_upload(
    settings: Settings,
    agent: AgentRecord,
    cache_key: str,
    filename: str,
    request: Request,
) -> GcodeCacheEntry:
    cache_key = validate_gcode_cache_key(cache_key)
    filename = normalize_gcode_filename(filename)
    expected_key = gcode_cache_key(agent.printer_id, filename)
    if cache_key != expected_key:
        raise HTTPException(status_code=409, detail="cache key não confere com o G-code informado")

    cache_dir = _printer_cache_dir(settings, agent.printer_id)
    cache_dir.mkdir(parents=True, exist_ok=True)
    data_path = _data_path(settings, agent.printer_id, cache_key)
    entry_path = _entry_path(settings, agent.printer_id, cache_key)
    temp_path = data_path.with_suffix(".gcode.tmp")

    digest = hashlib.sha256()
    size = 0
    try:
        with temp_path.open("wb") as file:
            async for chunk in request.stream():
                if not chunk:
                    continue
                size += len(chunk)
                if size > MAX_GCODE_CACHE_BYTES:
                    raise HTTPException(status_code=413, detail="G-code excede o limite de cache")
                digest.update(chunk)
                file.write(chunk)
        if size == 0:
            raise HTTPException(status_code=400, detail="G-code vazio")
        os.replace(temp_path, data_path)
        entry = GcodeCacheEntry(
            cache_key=cache_key,
            printer_id=agent.printer_id,
            filename=filename,
            size_bytes=size,
            sha256=digest.hexdigest(),
            created_at=_utc_now(),
        )
        entry_path.write_text(entry.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return entry
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


async def store_user_gcode_upload(
    settings: Settings,
    printer_id: int,
    filename: str,
    request: Request,
) -> GcodeUploadEntry:
    filename = normalize_gcode_filename(filename)
    upload_key = secrets.token_hex(32)
    upload_dir = _printer_upload_dir(settings, printer_id)
    upload_dir.mkdir(parents=True, exist_ok=True)
    data_path = _upload_data_path(settings, printer_id, upload_key)
    entry_path = _upload_entry_path(settings, printer_id, upload_key)
    temp_path = data_path.with_suffix(".gcode.tmp")
    digest = hashlib.sha256()
    size = 0
    try:
        with temp_path.open("wb") as file:
            async for chunk in request.stream():
                if not chunk:
                    continue
                size += len(chunk)
                if size > MAX_GCODE_CACHE_BYTES:
                    raise HTTPException(status_code=413, detail="G-code excede o limite de 96 MB")
                digest.update(chunk)
                file.write(chunk)
        if size == 0:
            raise HTTPException(status_code=400, detail="G-code vazio")
        os.replace(temp_path, data_path)
        entry = GcodeUploadEntry(
            upload_key=upload_key,
            printer_id=printer_id,
            filename=filename,
            size_bytes=size,
            sha256=digest.hexdigest(),
            created_at=_utc_now(),
        )
        entry_path.write_text(entry.model_dump_json(indent=2) + "\n", encoding="utf-8")
        return entry
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def read_gcode_upload_entry(settings: Settings, printer_id: int, upload_key: str) -> GcodeUploadEntry | None:
    upload_key = validate_gcode_cache_key(upload_key)
    entry_path = _upload_entry_path(settings, printer_id, upload_key)
    data_path = _upload_data_path(settings, printer_id, upload_key)
    if not entry_path.exists() or not data_path.exists():
        return None
    if _is_stale(entry_path):
        _remove_cache_files(entry_path, data_path)
        return None
    try:
        entry = GcodeUploadEntry.model_validate(json.loads(entry_path.read_text(encoding="utf-8")))
    except (OSError, json.JSONDecodeError, ValueError):
        _remove_cache_files(entry_path, data_path)
        return None
    if entry.printer_id != printer_id or entry.upload_key != upload_key:
        _remove_cache_files(entry_path, data_path)
        return None
    if data_path.stat().st_size != entry.size_bytes:
        _remove_cache_files(entry_path, data_path)
        return None
    return entry


def gcode_upload_file_response(settings: Settings, agent: AgentRecord, upload_key: str) -> FileResponse:
    entry = read_gcode_upload_entry(settings, agent.printer_id, upload_key)
    if entry is None:
        raise HTTPException(status_code=404, detail="upload G-code não encontrado ou expirado")
    data_path = _upload_data_path(settings, agent.printer_id, entry.upload_key)
    entry_path = _upload_entry_path(settings, agent.printer_id, entry.upload_key)
    return FileResponse(
        data_path,
        media_type="text/plain; charset=utf-8",
        filename=Path(entry.filename).name,
        headers={
            "X-Printora-Filename": entry.filename,
            "X-Printora-SHA256": entry.sha256,
        },
        background=BackgroundTask(_remove_cache_files, entry_path, data_path),
    )


def validate_gcode_cache_key(cache_key: str) -> str:
    value = cache_key.strip().lower()
    if not _CACHE_KEY_RE.fullmatch(value):
        raise HTTPException(status_code=400, detail="cache key inválida")
    return value


def _printer_cache_dir(settings: Settings, printer_id: int) -> Path:
    return settings.data_dir / "gcode_cache" / str(printer_id)


def _data_path(settings: Settings, printer_id: int, cache_key: str) -> Path:
    return _printer_cache_dir(settings, printer_id) / f"{cache_key}.gcode"


def _entry_path(settings: Settings, printer_id: int, cache_key: str) -> Path:
    return _printer_cache_dir(settings, printer_id) / f"{cache_key}.json"


def _printer_upload_dir(settings: Settings, printer_id: int) -> Path:
    return settings.data_dir / "gcode_uploads" / str(printer_id)


def _upload_data_path(settings: Settings, printer_id: int, upload_key: str) -> Path:
    return _printer_upload_dir(settings, printer_id) / f"{upload_key}.gcode"


def _upload_entry_path(settings: Settings, printer_id: int, upload_key: str) -> Path:
    return _printer_upload_dir(settings, printer_id) / f"{upload_key}.json"


def _is_stale(path: Path) -> bool:
    try:
        return datetime.now(timezone.utc).timestamp() - path.stat().st_mtime > GCODE_CACHE_TTL_SECONDS
    except OSError:
        return True


def _remove_cache_files(entry_path: Path, data_path: Path) -> None:
    entry_path.unlink(missing_ok=True)
    data_path.unlink(missing_ok=True)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
