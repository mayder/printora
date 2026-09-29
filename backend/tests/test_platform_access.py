from pathlib import Path

import pytest

from app.config import Settings, parse_platform_admin_emails
from app.platform_access import is_platform_admin


def test_platform_admin_emails_are_normalized_and_configurable(tmp_path: Path) -> None:
    settings = Settings(
        data_dir=tmp_path,
        platform_admin_emails=" Admin.One@example.test,admin.two@example.test ",
    )

    assert settings.platform_admin_email_set == frozenset(
        {"admin.one@example.test", "admin.two@example.test"}
    )
    assert is_platform_admin("ADMIN.ONE@EXAMPLE.TEST", settings)
    assert not is_platform_admin("ordinary@example.test", settings)


def test_empty_platform_admin_configuration_denies_everyone(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path, platform_admin_emails="")

    assert settings.platform_admin_email_set == frozenset()
    assert not is_platform_admin("admin@example.test", settings)


@pytest.mark.parametrize(
    "value",
    ["invalid", "@example.test", "admin@", "admin@example.test@evil.test", "admin @example.test"],
)
def test_invalid_platform_admin_configuration_fails_closed(value: str) -> None:
    with pytest.raises(ValueError):
        parse_platform_admin_emails(value)


def test_runtime_admin_checks_do_not_embed_an_identity() -> None:
    repository_root = Path(__file__).resolve().parents[2]
    runtime_roots = [repository_root / "backend" / "app", repository_root / "frontend" / "src"]
    offenders = [
        path.relative_to(repository_root).as_posix()
        for runtime_root in runtime_roots
        for path in runtime_root.rglob("*")
        if path.suffix in {".py", ".ts", ".tsx"}
        if path.name != "config.py" and "breno@mayder.com.br" in path.read_text(encoding="utf-8")
    ]

    assert offenders == []


def test_public_registration_rejects_configured_platform_admin(tmp_path: Path, monkeypatch) -> None:
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import app

    monkeypatch.setenv("PRINTORA_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("PRINTORA_PLATFORM_ADMIN_EMAILS", "platform-admin@example.test")
    get_settings.cache_clear()
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/auth/register",
                json={"email": "platform-admin@example.test", "password": "correct-horse"},
            )
        assert response.status_code == 403
        assert response.json()["detail"] == "conta administrativa deve ser provisionada por canal operacional"
    finally:
        get_settings.cache_clear()
