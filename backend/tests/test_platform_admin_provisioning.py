from pathlib import Path

import pytest

from app.modules.identity.platform_admin_provisioning import (
    provision_platform_admin,
    read_password,
)


def test_password_file_must_be_private(tmp_path: Path) -> None:
    password_file = tmp_path / "admin-password"
    password_file.write_text("synthetic-correct-horse\n", encoding="utf-8")
    password_file.chmod(0o640)

    with pytest.raises(ValueError, match="somente ao proprietário"):
        read_password(password_file)


def test_provision_requires_explicit_empty_database_initialization(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.setenv("PRINTORA_PLATFORM_ADMIN_EMAILS", "pentest-admin@example.test")
    password_file = tmp_path / "admin-password"
    password_file.write_text("synthetic-correct-horse\n", encoding="utf-8")
    password_file.chmod(0o600)

    with pytest.raises(ValueError, match="--initialize-empty"):
        provision_platform_admin(
            data_dir=tmp_path / "data",
            email="pentest-admin@example.test",
            password_file=password_file,
            display_name="Pentest Admin",
            initialize_empty=False,
        )


def test_provision_creates_synthetic_admin_once(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PRINTORA_PLATFORM_ADMIN_EMAILS", "pentest-admin@example.test")
    password_file = tmp_path / "admin-password"
    password_file.write_text("synthetic-correct-horse\n", encoding="utf-8")
    password_file.chmod(0o600)
    data_dir = tmp_path / "data"

    created = provision_platform_admin(
        data_dir=data_dir,
        email="PENTEST-ADMIN@EXAMPLE.TEST",
        password_file=password_file,
        display_name="Pentest Admin",
        initialize_empty=True,
    )
    repeated = provision_platform_admin(
        data_dir=data_dir,
        email="pentest-admin@example.test",
        password_file=password_file,
        display_name="Pentest Admin",
        initialize_empty=False,
    )

    assert created["created"] is True
    assert created["platform_admin"] is True
    assert repeated == {**created, "created": False}
