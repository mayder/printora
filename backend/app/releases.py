import json
import re
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field


ReleaseSourceMode = Literal["github", "fixture", "disabled"]
ReleaseStatus = Literal["ok", "offline", "rate_limited", "disabled", "error"]
UpdateAvailability = Literal["up_to_date", "outdated", "unknown"]


class ReleaseRecord(BaseModel):
    tag: str
    name: str
    channel: str
    changelog: str
    changelog_summary: str
    url: str | None = None
    published_at: str | None = None
    prerelease: bool = False
    draft: bool = False
    installed: bool = False


class ReleasesResponse(BaseModel):
    safe_mode: str = "read_only"
    source: ReleaseSourceMode
    status: ReleaseStatus
    channel: str
    installed_version: str
    update_status: UpdateAvailability
    latest_release_available: bool
    latest_release: ReleaseRecord | None = None
    releases: list[ReleaseRecord] = Field(default_factory=list)
    update_supported: bool = False
    message: str
    error: str | None = None


class GitHubReleaseClient:
    def __init__(
        self,
        *,
        owner: str,
        repo: str,
        api_base_url: str = "https://api.github.com",
        timeout_seconds: float = 5.0,
        fixture_path: Path | None = None,
    ) -> None:
        self.owner = owner.strip()
        self.repo = repo.strip()
        self.api_base_url = api_base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.fixture_path = fixture_path

    async def fetch_releases(self) -> list[dict[str, Any]]:
        if self.fixture_path is not None:
            return load_release_fixture(self.fixture_path)
        url = f"{self.api_base_url}/repos/{self.owner}/{self.repo}/releases"
        headers = {"Accept": "application/vnd.github+json"}
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            payload = response.json()
        if not isinstance(payload, list):
            raise ValueError("GitHub releases response must be a list")
        return [item for item in payload if isinstance(item, dict)]


def load_release_fixture(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("release fixture must be a JSON list")
    return [item for item in payload if isinstance(item, dict)]


def build_releases_response(
    *,
    raw_releases: list[dict[str, Any]],
    source: ReleaseSourceMode,
    channel: str,
    installed_version: str | None = None,
) -> ReleasesResponse:
    clean_installed = installed_version or installed_app_version()
    releases = parse_releases(raw_releases, channel=channel, installed_version=clean_installed)
    latest_release = latest_production_release(releases)
    if latest_release and latest_release.installed:
        update_status: UpdateAvailability = "up_to_date"
        message = "Versão instalada já é a release mais recente."
    elif latest_release:
        update_status = "outdated"
        message = "Release disponível para revisão."
    else:
        update_status = "unknown"
        message = "Nenhuma release de produção encontrada."
    return ReleasesResponse(
        source=source,
        status="ok",
        channel=channel,
        installed_version=clean_installed,
        update_status=update_status,
        latest_release_available=latest_release is not None and not latest_release.installed,
        latest_release=latest_release,
        releases=releases,
        message=message,
    )


def build_unavailable_releases_response(
    *,
    source: ReleaseSourceMode,
    channel: str,
    status: ReleaseStatus,
    error: str | None = None,
    installed_version: str | None = None,
) -> ReleasesResponse:
    if status == "disabled":
        message = "Consulta de releases desabilitada."
    elif status == "rate_limited":
        message = "Limite de consulta do GitHub atingido."
    elif status == "offline":
        message = "Não foi possível consultar releases agora."
    else:
        message = "Falha ao consultar releases."
    return ReleasesResponse(
        source=source,
        status=status,
        channel=channel,
        installed_version=installed_version or installed_app_version(),
        update_status="unknown",
        latest_release_available=False,
        message=message,
        error=error,
    )


def parse_releases(
    raw_releases: list[dict[str, Any]],
    *,
    channel: str,
    installed_version: str,
) -> list[ReleaseRecord]:
    records = [_parse_release(item, channel=channel, installed_version=installed_version) for item in raw_releases]
    production = [item for item in records if not item.draft and _matches_channel(item, channel)]
    return sorted(production, key=_release_sort_key, reverse=True)


def latest_production_release(releases: list[ReleaseRecord]) -> ReleaseRecord | None:
    for release in releases:
        if not release.draft and not release.prerelease:
            return release
    return releases[0] if releases else None


def installed_app_version() -> str:
    try:
        return metadata.version("printora-backend")
    except metadata.PackageNotFoundError:
        return "0.1.0"


def _parse_release(raw: dict[str, Any], *, channel: str, installed_version: str) -> ReleaseRecord:
    tag = _string(raw.get("tag_name")) or _string(raw.get("tag")) or "unknown"
    name = _string(raw.get("name")) or tag
    prerelease = bool(raw.get("prerelease"))
    draft = bool(raw.get("draft"))
    release_channel = _channel_for_release(tag, prerelease)
    changelog = _sanitize_release_text(_string(raw.get("body")) or "")
    return ReleaseRecord(
        tag=tag,
        name=name,
        channel=release_channel,
        changelog=changelog,
        changelog_summary=_summarize_changelog(changelog),
        url=_string(raw.get("html_url")),
        published_at=_string(raw.get("published_at")),
        prerelease=prerelease,
        draft=draft,
        installed=_normalize_version(tag) == _normalize_version(installed_version),
    )


def _matches_channel(release: ReleaseRecord, channel: str) -> bool:
    if channel == "all":
        return True
    if channel in {"stable", "production"}:
        return not release.prerelease
    return release.channel == channel


def _channel_for_release(tag: str, prerelease: bool) -> str:
    if prerelease:
        lowered = tag.lower()
        if "beta" in lowered:
            return "beta"
        if "alpha" in lowered:
            return "alpha"
        return "prerelease"
    return "stable"


def _release_sort_key(release: ReleaseRecord) -> tuple[datetime, str]:
    return (_parse_datetime(release.published_at), release.tag)


def _parse_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)


def _normalize_version(value: str) -> str:
    return value.strip().lower().removeprefix("v")


def _string(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _summarize_changelog(value: str, *, max_chars: int = 280) -> str:
    lines = [line.strip(" -\t") for line in value.splitlines() if line.strip()]
    summary = " ".join(lines)
    if len(summary) <= max_chars:
        return summary
    return summary[: max_chars - 1].rstrip() + "…"


def _sanitize_release_text(value: str) -> str:
    without_package_prefix = re.sub(r"\bPKG-\d+\s*:\s*", "", value, flags=re.IGNORECASE)
    without_package_ids = re.sub(r"\bPKG-\d+\b", "entrega", without_package_prefix, flags=re.IGNORECASE)
    return re.sub(r"\blote\s+\d+\b", "etapa", without_package_ids, flags=re.IGNORECASE)
