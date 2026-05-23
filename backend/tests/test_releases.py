from pathlib import Path
import asyncio

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.releases import (
    GitHubReleaseClient,
    build_releases_response,
    build_unavailable_releases_response,
    latest_production_release,
    load_release_fixture,
    parse_releases,
)


FIXTURE = Path(__file__).parent / "fixtures" / "github_releases.json"
CURRENT_FIXTURE = Path(__file__).parent / "fixtures" / "github_releases_current.json"
LONG_CHANGELOG_FIXTURE = Path(__file__).parent / "fixtures" / "github_releases_long_changelog.json"


def test_parse_releases_filters_drafts_and_marks_installed_version() -> None:
    raw = load_release_fixture(FIXTURE)

    releases = parse_releases(raw, channel="stable", installed_version="0.1.0")

    assert [release.tag for release in releases] == ["v0.2.0", "v0.1.0"]
    assert releases[0].changelog == "Correcoes de manutencao e configuracao."
    assert releases[0].changelog_summary == "Correcoes de manutencao e configuracao."
    assert releases[0].channel == "stable"
    assert releases[1].installed is True


def test_latest_release_uses_latest_stable_production_release() -> None:
    raw = load_release_fixture(FIXTURE)
    response = build_releases_response(
        raw_releases=raw,
        source="fixture",
        channel="stable",
        installed_version="0.1.0",
    )

    assert response.status == "ok"
    assert response.update_status == "outdated"
    assert response.latest_release_available is True
    assert response.update_supported is False
    assert response.latest_release is not None
    assert response.latest_release.tag == "v0.2.0"
    assert latest_production_release(response.releases).tag == "v0.2.0"
    assert response.message == "Release disponível para revisão."


def test_release_response_reports_installed_when_latest_matches_current() -> None:
    raw = load_release_fixture(CURRENT_FIXTURE)
    response = build_releases_response(
        raw_releases=raw,
        source="fixture",
        channel="stable",
        installed_version="v0.1.0",
    )

    assert response.latest_release is not None
    assert response.latest_release.installed is True
    assert response.update_status == "up_to_date"
    assert response.latest_release_available is False
    assert response.message == "Versão instalada já é a release mais recente."


def test_release_changelog_summary_is_bounded() -> None:
    raw = load_release_fixture(LONG_CHANGELOG_FIXTURE)

    releases = parse_releases(raw, channel="stable", installed_version="0.1.0")

    assert len(releases) == 1
    assert len(releases[0].changelog_summary) <= 280
    assert releases[0].changelog_summary.endswith("…")


def test_github_release_client_reports_network_error_without_update(monkeypatch) -> None:
    client = GitHubReleaseClient(owner="mayder", repo="printora", timeout_seconds=0.01)

    async def fail_get(*args, **kwargs):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr(httpx.AsyncClient, "get", fail_get)

    async def fetch() -> None:
        with pytest.raises(httpx.ConnectError):
            await client.fetch_releases()

    asyncio.run(fetch())

    response = build_unavailable_releases_response(
        source="github",
        channel="stable",
        status="offline",
        error="network down",
        installed_version="0.1.0",
    )
    assert response.safe_mode == "read_only"
    assert response.update_supported is False
    assert response.status == "offline"
    assert response.error == "network down"


def test_system_releases_endpoint_supports_fixture_mode(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_RELEASE_SOURCE_MODE", "fixture")
    monkeypatch.setenv("PRINTORA_RELEASE_FIXTURE_PATH", str(FIXTURE))
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.get("/api/system/releases")
        payload = response.json()
        assert response.status_code == 200
        assert payload["safe_mode"] == "read_only"
        assert payload["source"] == "fixture"
        assert payload["channel"] == "stable"
        assert payload["update_status"] == "outdated"
        assert payload["latest_release_available"] is True
        assert payload["latest_release"]["tag"] == "v0.2.0"
        assert payload["latest_release"]["changelog_summary"] == "Correcoes de manutencao e configuracao."
        assert payload["update_supported"] is False
    finally:
        get_settings.cache_clear()


def test_system_update_status_endpoint_is_read_only_and_reports_outdated(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_RELEASE_SOURCE_MODE", "fixture")
    monkeypatch.setenv("PRINTORA_RELEASE_FIXTURE_PATH", str(FIXTURE))
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.get("/api/system/update/status")
        payload = response.json()
        assert response.status_code == 200
        assert payload["safe_mode"] == "read_only"
        assert payload["update_supported"] is True
        assert payload["environment"] in {"android_termux", "unix"}
        assert payload["status"] == "ok"
        assert payload["update_status"] == "outdated"
        assert payload["channel"] == "stable"
        assert payload["latest_release_available"] is True
        assert payload["latest_release"]["tag"] == "v0.2.0"
    finally:
        get_settings.cache_clear()


def test_system_releases_endpoint_handles_github_rate_limit(tmp_path: Path, monkeypatch) -> None:
    observed_headers: dict[str, str] = {}

    async def rate_limited_get(self, url, headers=None):
        observed_headers.update(headers or {})
        request = httpx.Request("GET", url)
        return httpx.Response(
            403,
            headers={"x-ratelimit-remaining": "0"},
            json={"message": "API rate limit exceeded"},
            request=request,
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", rate_limited_get)
    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_RELEASE_SOURCE_MODE", "github")
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.get("/api/system/releases")
        payload = response.json()
        assert response.status_code == 200
        assert payload["safe_mode"] == "read_only"
        assert payload["status"] == "rate_limited"
        assert payload["update_status"] == "unknown"
        assert payload["latest_release_available"] is False
        assert payload["update_supported"] is False
        assert "Authorization" not in observed_headers
    finally:
        get_settings.cache_clear()
