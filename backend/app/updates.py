from typing import Any, Literal

from pydantic import BaseModel, Field


UpdateAction = Literal["refresh", "update"]
UpdateStatus = Literal["up_to_date", "update_available", "warning", "busy", "unknown"]


class UpdateComponent(BaseModel):
    name: str
    title: str
    configured_type: str
    status: UpdateStatus
    current_version: str | None = None
    remote_version: str | None = None
    full_version: str | None = None
    is_dirty: bool | None = None
    is_valid: bool | None = None
    commits_behind_count: int = 0
    package_count: int = 0
    warnings: list[str] = Field(default_factory=list)
    anomalies: list[str] = Field(default_factory=list)
    can_update: bool = True


class UpdateStatusResponse(BaseModel):
    safe_mode: str
    busy: bool
    github_requests_remaining: int | None = None
    github_rate_limit: int | None = None
    summary: str
    counts: dict[str, int]
    components: list[UpdateComponent]


class UpdateRunRequest(BaseModel):
    target: str = Field(min_length=1, max_length=80)


class UpdateRefreshRequest(BaseModel):
    name: str | None = Field(default=None, max_length=80)


class UpdateActionResponse(BaseModel):
    safe_mode: str
    action: UpdateAction
    target: str
    accepted: bool
    message: str
    result: dict[str, Any]


def build_update_status(raw_status: dict[str, Any]) -> UpdateStatusResponse:
    version_info = raw_status.get("version_info")
    components = []
    if isinstance(version_info, dict):
        components = [
            _build_component(name, value)
            for name, value in sorted(version_info.items(), key=lambda item: _component_sort_key(item[0]))
            if isinstance(value, dict)
        ]

    busy = bool(raw_status.get("busy"))
    counts = {
        "update_available": sum(1 for item in components if item.status == "update_available"),
        "warning": sum(1 for item in components if item.status == "warning"),
        "up_to_date": sum(1 for item in components if item.status == "up_to_date"),
        "unknown": sum(1 for item in components if item.status == "unknown"),
    }
    if busy:
        summary = "Update Manager ocupado"
    elif counts["warning"]:
        summary = "Há componentes com alerta"
    elif counts["update_available"]:
        summary = f"{counts['update_available']} componente(s) com update disponível"
    elif components:
        summary = "Tudo atualizado"
    else:
        summary = "Update Manager sem dados"

    return UpdateStatusResponse(
        safe_mode="moonraker_update_manager",
        busy=busy,
        github_requests_remaining=_optional_int(raw_status.get("github_requests_remaining")),
        github_rate_limit=_optional_int(raw_status.get("github_rate_limit")),
        summary=summary,
        counts=counts,
        components=components,
    )


def update_route_for_target(target: str) -> tuple[str, str]:
    clean_target = target.strip()
    if clean_target == "all":
        return "/machine/update/full", "all"
    if clean_target == "system":
        return "/machine/update/system", "system"
    if clean_target in {"klipper", "moonraker"}:
        return f"/machine/update/{clean_target}", clean_target
    return "/machine/update/client", clean_target


def _build_component(name: str, payload: dict[str, Any]) -> UpdateComponent:
    warnings = _string_list(payload.get("warnings"))
    anomalies = _string_list(payload.get("anomalies"))
    commits_behind_count = _commits_behind_count(payload)
    package_count = _optional_int(payload.get("package_count")) or 0
    current_version = _optional_str(payload.get("version"))
    remote_version = _optional_str(payload.get("remote_version"))
    is_dirty = _optional_bool(payload.get("is_dirty"))
    is_valid = _optional_bool(payload.get("is_valid"))

    status: UpdateStatus
    if warnings or anomalies or is_dirty or is_valid is False:
        status = "warning"
    elif commits_behind_count > 0 or package_count > 0 or _version_differs(current_version, remote_version):
        status = "update_available"
    elif current_version or name == "system":
        status = "up_to_date"
    else:
        status = "unknown"

    return UpdateComponent(
        name=name,
        title=_title_for_component(name),
        configured_type=str(payload.get("configured_type") or "unknown"),
        status=status,
        current_version=current_version,
        remote_version=remote_version,
        full_version=_optional_str(payload.get("full_version_string")),
        is_dirty=is_dirty,
        is_valid=is_valid,
        commits_behind_count=commits_behind_count,
        package_count=package_count,
        warnings=warnings,
        anomalies=anomalies,
        can_update=True,
    )


def _component_sort_key(name: str) -> tuple[int, str]:
    order = {
        "klipper": 0,
        "moonraker": 1,
        "mainsail": 2,
        "mainsail-config": 3,
        "system": 99,
    }
    return (order.get(name, 50), name)


def _title_for_component(name: str) -> str:
    labels = {
        "klipper": "Klipper",
        "moonraker": "Moonraker",
        "mainsail": "Mainsail",
        "mainsail-config": "Mainsail Config",
        "system": "Sistema",
    }
    return labels.get(name, name.replace("-", " ").title())


def _commits_behind_count(payload: dict[str, Any]) -> int:
    explicit = _optional_int(payload.get("commits_behind_count"))
    if explicit is not None:
        return explicit
    commits_behind = payload.get("commits_behind")
    if isinstance(commits_behind, list):
        return len(commits_behind)
    return 0


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _optional_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return None


def _optional_bool(value: object) -> bool | None:
    return value if isinstance(value, bool) else None


def _version_differs(current_version: str | None, remote_version: str | None) -> bool:
    return bool(current_version and remote_version and current_version != remote_version)
