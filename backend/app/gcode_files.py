from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class GcodeFileThumbnail(BaseModel):
    data_uri: str | None = None
    width: int | None = None
    height: int | None = None
    source: str | None = None


class GcodeFileEntry(BaseModel):
    filename: str
    path: str
    name: str
    directory: str = ""
    size: float | None = None
    modified: float | None = None
    estimated_time: float | None = None
    slicer: str | None = None
    slicer_version: str | None = None
    object_height: float | None = None
    layer_height: float | None = None
    first_layer_height: float | None = None
    layer_count: int | None = None
    nozzle_diameter: float | None = None
    filament_total: float | None = None
    filament_weight_total: float | None = None
    filament_type: str | None = None
    filament_name: str | None = None
    first_layer_bed_temp: float | None = None
    first_layer_extr_temp: float | None = None
    print_start_time: float | None = None
    print_end_time: float | None = None
    last_print_duration: float | None = None
    metadata_available: bool = False
    thumbnail: GcodeFileThumbnail | None = None


class GcodeDirectoryEntry(BaseModel):
    path: str
    name: str
    parent: str = ""
    file_count: int = 0
    total_size: float | None = None
    modified: float | None = None


class GcodeStorage(BaseModel):
    total: float | None = None
    used: float | None = None
    free: float | None = None


class GcodeFilesResponse(BaseModel):
    printer_id: int
    safe_mode: str = "read_only"
    data_state: Literal["live", "cached", "offline", "error", "unsupported"] = "live"
    root: str = "gcodes"
    summary: str
    files: list[GcodeFileEntry] = Field(default_factory=list)
    directories: list[GcodeDirectoryEntry] = Field(default_factory=list)
    storage: GcodeStorage | None = None
    fetched_at: str | None = None
    cache_ttl_seconds: int | None = None
    error: str | None = None
    agent: dict[str, Any] | None = None


GCODE_FILE_EXTENSIONS = (".gcode", ".gcode.gz", ".gco", ".g", ".gc", ".nc", ".ngc", ".tap")


def build_gcode_files_response(
    printer_id: int,
    payload: dict[str, Any] | None,
    *,
    agent: dict[str, Any] | None = None,
) -> GcodeFilesResponse:
    source = payload if isinstance(payload, dict) else {}
    files = _normalize_files(source.get("files"))
    directories = _normalize_directories(source.get("directories"), files)
    data_state = _data_state(source.get("data_state") or ("cached" if source.get("cache_state") == "hit" else "live"))
    summary = _text(source.get("summary")) or _files_summary(files, directories, data_state)
    return GcodeFilesResponse(
        printer_id=printer_id,
        safe_mode=_text(source.get("safe_mode")) or "read_only",
        data_state=data_state,
        root=_text(source.get("root")) or "gcodes",
        summary=summary,
        files=files,
        directories=directories,
        storage=_storage(source.get("storage")),
        fetched_at=_text(source.get("fetched_at")) or None,
        cache_ttl_seconds=_int_or_none(source.get("cache_ttl_seconds")),
        error=_text(source.get("error")) or None,
        agent=agent,
    )


def build_gcode_files_unavailable_response(
    printer_id: int,
    detail: str,
    *,
    agent: dict[str, Any] | None = None,
    data_state: Literal["offline", "error", "unsupported"] = "offline",
) -> GcodeFilesResponse:
    return GcodeFilesResponse(
        printer_id=printer_id,
        data_state=data_state,
        summary="Arquivos G-code indisponíveis nesta leitura.",
        files=[],
        directories=[],
        storage=None,
        error=detail,
        agent=agent,
    )


def _normalize_files(value: Any) -> list[GcodeFileEntry]:
    files: list[GcodeFileEntry] = []
    for item in value if isinstance(value, list) else []:
        mapped = item if isinstance(item, dict) else {}
        filename = _text(mapped.get("filename") or mapped.get("path") or mapped.get("name"))
        path = _text(mapped.get("path") or filename)
        if not _is_gcode_filename(filename or path):
            continue
        normalized_path = _normalize_path(path or filename)
        display_name = _basename(normalized_path)
        directory = _dirname(normalized_path)
        files.append(
            GcodeFileEntry(
                filename=filename or normalized_path,
                path=normalized_path,
                name=display_name,
                directory=directory,
                size=_number_or_none(mapped.get("size")),
                modified=_number_or_none(mapped.get("modified")),
                estimated_time=_number_or_none(mapped.get("estimated_time")),
                slicer=_text(mapped.get("slicer")) or None,
                slicer_version=_text(mapped.get("slicer_version")) or None,
                object_height=_number_or_none(mapped.get("object_height")),
                layer_height=_number_or_none(mapped.get("layer_height")),
                first_layer_height=_number_or_none(mapped.get("first_layer_height")),
                layer_count=_int_or_none(mapped.get("layer_count") or mapped.get("layers") or mapped.get("total_layers")),
                nozzle_diameter=_number_or_none(mapped.get("nozzle_diameter")),
                filament_total=_number_or_none(mapped.get("filament_total")),
                filament_weight_total=_number_or_none(mapped.get("filament_weight_total")),
                filament_type=_text(mapped.get("filament_type")) or None,
                filament_name=_text(mapped.get("filament_name")) or None,
                first_layer_bed_temp=_number_or_none(mapped.get("first_layer_bed_temp")),
                first_layer_extr_temp=_number_or_none(mapped.get("first_layer_extr_temp")),
                print_start_time=_number_or_none(mapped.get("print_start_time")),
                print_end_time=_number_or_none(mapped.get("print_end_time")),
                last_print_duration=_number_or_none(mapped.get("last_print_duration")),
                metadata_available=bool(mapped.get("metadata_available")),
                thumbnail=_thumbnail(mapped.get("thumbnail")),
            )
        )
    files.sort(key=lambda item: item.modified if isinstance(item.modified, int | float) else 0, reverse=True)
    return files


def _normalize_directories(value: Any, files: list[GcodeFileEntry]) -> list[GcodeDirectoryEntry]:
    by_path: dict[str, GcodeDirectoryEntry] = {}
    for item in value if isinstance(value, list) else []:
        mapped = item if isinstance(item, dict) else {}
        path = _normalize_path(_text(mapped.get("path") or mapped.get("name")))
        if not path:
            continue
        by_path[path] = GcodeDirectoryEntry(
            path=path,
            name=_basename(path),
            parent=_dirname(path),
            file_count=_int_or_none(mapped.get("file_count")) or 0,
            total_size=_number_or_none(mapped.get("total_size") or mapped.get("size")),
            modified=_number_or_none(mapped.get("modified")),
        )
    for file in files:
        parts = [part for part in file.directory.split("/") if part]
        for index in range(1, len(parts) + 1):
            path = "/".join(parts[:index])
            entry = by_path.get(path)
            if entry is None:
                entry = GcodeDirectoryEntry(path=path, name=parts[index - 1], parent="/".join(parts[: index - 1]))
                by_path[path] = entry
            entry.file_count += 1
            if isinstance(file.size, int | float):
                entry.total_size = (entry.total_size or 0) + file.size
            if isinstance(file.modified, int | float):
                entry.modified = max(entry.modified or 0, file.modified)
    return sorted(by_path.values(), key=lambda item: item.path.lower())


def _storage(value: Any) -> GcodeStorage | None:
    mapped = value if isinstance(value, dict) else {}
    total = _number_or_none(mapped.get("total"))
    used = _number_or_none(mapped.get("used"))
    free = _number_or_none(mapped.get("free"))
    if total is None and used is None and free is None:
        return None
    return GcodeStorage(total=total, used=used, free=free)


def _thumbnail(value: Any) -> GcodeFileThumbnail | None:
    mapped = value if isinstance(value, dict) else {}
    data_uri = _text(mapped.get("data_uri"))
    source = _text(mapped.get("source"))
    width = _int_or_none(mapped.get("width"))
    height = _int_or_none(mapped.get("height"))
    if not any((data_uri, source, width, height)):
        return None
    return GcodeFileThumbnail(data_uri=data_uri or None, width=width, height=height, source=source or None)


def _files_summary(files: list[GcodeFileEntry], directories: list[GcodeDirectoryEntry], data_state: str) -> str:
    if data_state in {"offline", "error", "unsupported"}:
        return "Arquivos G-code indisponíveis nesta leitura."
    if not files:
        return "Nenhum arquivo G-code retornado pelo Moonraker."
    folder_text = f" em {len(directories)} pasta(s)" if directories else ""
    return f"{len(files)} arquivo(s) G-code{folder_text}."


def _data_state(value: Any) -> Literal["live", "cached", "offline", "error", "unsupported"]:
    text = _text(value)
    if text in {"live", "cached", "offline", "error", "unsupported"}:
        return text  # type: ignore[return-value]
    return "live"


def _normalize_path(value: str) -> str:
    return "/".join(part for part in value.strip().replace("\\", "/").split("/") if part and part != ".")


def _basename(value: str) -> str:
    return value.split("/")[-1] if value else ""


def _dirname(value: str) -> str:
    parts = [part for part in value.split("/") if part]
    return "/".join(parts[:-1])


def _is_gcode_filename(value: str) -> bool:
    lowered = value.strip().lower()
    return any(lowered.endswith(extension) for extension in GCODE_FILE_EXTENSIONS)


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list | tuple):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return ""


def _number_or_none(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return float(value)
    return None


def _int_or_none(value: Any) -> int | None:
    number = _number_or_none(value)
    if number is None:
        return None
    return int(number)
