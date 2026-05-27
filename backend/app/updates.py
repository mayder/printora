from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.database import connect_database


UpdateAction = Literal["refresh", "update", "rollback"]
UpdateRiskLevel = Literal["normal", "caution", "high"]
UpdateStatus = Literal["up_to_date", "update_available", "warning", "busy", "unknown"]
RISK_UPDATE_CONFIRMATION_PHRASE = "ATUALIZAR COM RISCO"
ROLLBACK_CONFIRMATION_PHRASE = "ROLLBACK UPDATE"


class UpdateComponent(BaseModel):
    name: str
    title: str
    configured_type: str
    repo_url: str | None = None
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
    rollback_version: str | None = None
    can_rollback: bool = False
    risk_level: UpdateRiskLevel = "normal"
    risk_reason: str | None = None
    requires_confirmation: bool = False
    alert_silenced: bool = False
    alert_silence_id: int | None = None


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
    confirmation_phrase: str | None = Field(default=None, max_length=120)


class PrinterUpdateRollbackRequest(BaseModel):
    target: str = Field(min_length=1, max_length=80)
    confirmation_phrase: str = Field(min_length=1, max_length=120)


class UpdateRefreshRequest(BaseModel):
    name: str | None = Field(default=None, max_length=80)


class UpdateSilenceRequest(BaseModel):
    target: str = Field(min_length=1, max_length=80)
    current_version: str | None = Field(default=None, max_length=160)
    remote_version: str | None = Field(default=None, max_length=160)
    full_version: str | None = Field(default=None, max_length=240)
    commits_behind_count: int = Field(default=0, ge=0)
    package_count: int = Field(default=0, ge=0)
    warnings: list[str] = Field(default_factory=list)
    anomalies: list[str] = Field(default_factory=list)
    reason: str | None = Field(default=None, max_length=240)


class UpdateSilenceResponse(BaseModel):
    safe_mode: str
    target: str
    silenced: bool
    message: str
    silence_id: int | None = None


class UpdateActionResponse(BaseModel):
    safe_mode: str
    action: UpdateAction
    target: str
    accepted: bool
    message: str
    result: dict[str, Any]


@dataclass(frozen=True)
class UpdateAlertSilence:
    id: int
    printer_id: int
    component_name: str
    version_key: str
    current_version: str | None
    remote_version: str | None
    full_version: str | None
    reason: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class UpdateAlertSilenceRepository:
    database_path: Path

    def list_for_printer(self, printer_id: int) -> list[UpdateAlertSilence]:
        with connect_database(self.database_path) as connection:
            rows = connection.execute(
                """
                SELECT id, printer_id, component_name, version_key, current_version, remote_version,
                       full_version, reason, created_at, updated_at
                FROM update_alert_silences
                WHERE printer_id = ?
                """,
                (printer_id,),
            ).fetchall()
        return [_silence_from_row(row) for row in rows]

    def silence_component(
        self,
        printer_id: int,
        component_name: str,
        component_payload: dict[str, Any],
        reason: str | None = None,
    ) -> UpdateAlertSilence:
        version_key = update_component_version_key(component_name, component_payload)
        current_version = _optional_str(component_payload.get("version"))
        remote_version = _optional_str(component_payload.get("remote_version"))
        full_version = _optional_str(component_payload.get("full_version_string"))
        clean_reason = reason.strip() if reason else None
        with connect_database(self.database_path) as connection:
            connection.execute(
                """
                INSERT INTO update_alert_silences (
                    printer_id, component_name, version_key, current_version, remote_version,
                    full_version, reason
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(printer_id, component_name, version_key) DO UPDATE SET
                    current_version = excluded.current_version,
                    remote_version = excluded.remote_version,
                    full_version = excluded.full_version,
                    reason = excluded.reason,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    printer_id,
                    component_name,
                    version_key,
                    current_version,
                    remote_version,
                    full_version,
                    clean_reason,
                ),
            )
        record = self.get_matching(printer_id, component_name, version_key)
        if record is None:
            raise RuntimeError("update silence was not persisted")
        return record

    def delete_matching(self, printer_id: int, component_name: str, version_key: str | None = None) -> int:
        with connect_database(self.database_path) as connection:
            if version_key:
                cursor = connection.execute(
                    """
                    DELETE FROM update_alert_silences
                    WHERE printer_id = ? AND component_name = ? AND version_key = ?
                    """,
                    (printer_id, component_name, version_key),
                )
            else:
                cursor = connection.execute(
                    """
                    DELETE FROM update_alert_silences
                    WHERE printer_id = ? AND component_name = ?
                    """,
                    (printer_id, component_name),
                )
        return int(cursor.rowcount or 0)

    def get_matching(self, printer_id: int, component_name: str, version_key: str) -> UpdateAlertSilence | None:
        with connect_database(self.database_path) as connection:
            row = connection.execute(
                """
                SELECT id, printer_id, component_name, version_key, current_version, remote_version,
                       full_version, reason, created_at, updated_at
                FROM update_alert_silences
                WHERE printer_id = ? AND component_name = ? AND version_key = ?
                """,
                (printer_id, component_name, version_key),
            ).fetchone()
        return _silence_from_row(row) if row else None


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
    active_components = [item for item in components if not item.alert_silenced]
    counts = {
        "update_available": sum(1 for item in active_components if item.status == "update_available"),
        "warning": sum(1 for item in active_components if item.status == "warning"),
        "up_to_date": sum(1 for item in active_components if item.status == "up_to_date"),
        "unknown": sum(1 for item in active_components if item.status == "unknown"),
        "silenced": sum(1 for item in components if item.alert_silenced),
    }
    if busy:
        summary = "Update Manager ocupado"
    elif counts["warning"]:
        summary = "Há componentes com alerta"
    elif counts["update_available"]:
        summary = f"{counts['update_available']} componente(s) com update disponível"
    elif counts["silenced"]:
        summary = "Updates silenciados"
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


def risky_update_components(status: UpdateStatusResponse, target: str) -> list[UpdateComponent]:
    clean_target = target.strip()
    if clean_target == "all":
        candidates = [item for item in status.components if item.can_update]
    else:
        candidates = [item for item in status.components if item.name == clean_target and item.can_update]
    return [item for item in candidates if item.requires_confirmation]


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
    rollback_version = _optional_str(payload.get("rollback_version"))
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

    risk_level, risk_reason = _update_risk(name)
    requires_confirmation = status in {"update_available", "warning"} and risk_level == "high"

    return UpdateComponent(
        name=name,
        title=_title_for_component(name),
        configured_type=str(payload.get("configured_type") or "unknown"),
        repo_url=_repository_url(payload),
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
        can_update=status in {"update_available", "warning"},
        rollback_version=rollback_version,
        can_rollback=bool(rollback_version and rollback_version != current_version),
        risk_level=risk_level,
        risk_reason=risk_reason,
        requires_confirmation=requires_confirmation,
        alert_silenced=bool(payload.get("printora_alert_silenced")),
        alert_silence_id=_optional_int(payload.get("printora_alert_silence_id")),
    )


def _repository_url(payload: dict[str, Any]) -> str | None:
    raw_url = _optional_str(payload.get("remote_url")) or _optional_str(payload.get("recovery_url"))
    if raw_url:
        normalized_url = _normalize_repository_url(raw_url)
        if normalized_url:
            return normalized_url
    owner = _optional_str(payload.get("owner"))
    repo_name = _optional_str(payload.get("repo_name"))
    if owner and repo_name:
        return f"https://github.com/{owner}/{repo_name.removesuffix('.git')}"
    return None


def _normalize_repository_url(raw_url: str) -> str | None:
    clean_url = raw_url.strip()
    if clean_url.startswith("git@github.com:"):
        clean_url = f"https://github.com/{clean_url.removeprefix('git@github.com:')}"
    if clean_url.startswith("https://") or clean_url.startswith("http://"):
        return clean_url.removesuffix(".git")
    return None


def apply_update_alert_silences(raw_status: dict[str, Any], silences: list[UpdateAlertSilence]) -> dict[str, Any]:
    version_info = raw_status.get("version_info")
    if not isinstance(version_info, dict) or not silences:
        return raw_status
    silence_map = {(item.component_name, item.version_key): item for item in silences}
    for name, payload in version_info.items():
        if not isinstance(payload, dict):
            continue
        silence = silence_map.get((str(name), update_component_version_key(str(name), payload)))
        if silence is None:
            continue
        payload["printora_alert_silenced"] = True
        payload["printora_alert_silence_id"] = silence.id
    return raw_status


def update_component_version_key(name: str, payload: dict[str, Any]) -> str:
    identity = {
        "name": name,
        "version": _optional_str(payload.get("version")),
        "remote_version": _optional_str(payload.get("remote_version")),
        "full_version_string": _optional_str(payload.get("full_version_string")),
        "commits_behind_count": _commits_behind_count(payload),
        "package_count": _optional_int(payload.get("package_count")) or 0,
        "warnings": _string_list(payload.get("warnings")),
        "anomalies": _string_list(payload.get("anomalies")),
    }
    encoded = json.dumps(identity, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def is_update_alert_silenced(repo: dict[str, Any]) -> bool:
    return bool(repo.get("printora_alert_silenced"))


def _update_risk(name: str) -> tuple[UpdateRiskLevel, str | None]:
    normalized = name.lower().replace("_", "-")
    if normalized == "klipper":
        return (
            "high",
            "Klipper pode quebrar compatibilidade com extras, plugins de toolchanger, probe, macros e módulos customizados.",
        )
    if "toolchanger" in normalized or normalized.startswith("ktc"):
        return (
            "high",
            "Plugin de toolchanger depende de APIs internas do Klipper; versões incompatíveis podem impedir o Klipper de iniciar.",
        )
    return "normal", None


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


def _silence_from_row(row: Any) -> UpdateAlertSilence:
    return UpdateAlertSilence(
        id=int(row["id"]),
        printer_id=int(row["printer_id"]),
        component_name=str(row["component_name"]),
        version_key=str(row["version_key"]),
        current_version=_optional_str(row["current_version"]),
        remote_version=_optional_str(row["remote_version"]),
        full_version=_optional_str(row["full_version"]),
        reason=_optional_str(row["reason"]),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
    )
