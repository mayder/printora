from functools import lru_cache
import os
from pathlib import Path
import platform
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

HostAuditMode = Literal["disabled", "local", "ssh"]
FirmwareBuildMode = Literal["disabled", "local"]
ReleaseSourceMode = Literal["github", "fixture", "disabled"]
ObjectStorageMode = Literal["local", "s3"]
PaymentMode = Literal["disabled", "sandbox"]


class Settings(BaseSettings):
    app_name: str = "Printora"
    moonraker_url: str = Field(default="http://127.0.0.1:7125")
    data_dir: Path = Field(default_factory=lambda: _default_data_dir())
    frontend_dist_dir: Path = Field(default=Path(__file__).resolve().parents[2] / "frontend" / "dist")
    request_timeout_seconds: float = 5.0
    host_audit_mode: HostAuditMode = "local"
    host_audit_ssh_target: str = "pi@voron.local"
    host_audit_timeout_seconds: float = 12.0
    firmware_build_mode: FirmwareBuildMode = "disabled"
    firmware_build_timeout_seconds: float = 900.0
    release_source_mode: ReleaseSourceMode = "github"
    release_github_owner: str = "mayder"
    release_github_repo: str = "printora"
    release_github_api_base_url: str = "https://api.github.com"
    release_channel: str = "stable"
    release_fixture_path: Path | None = None
    release_request_timeout_seconds: float = 5.0
    self_update_script_path: Path | None = None
    self_update_android_script_path: Path = Field(default=Path(__file__).resolve().parents[2] / "scripts" / "android_update_printora.sh")
    self_update_unix_script_path: Path = Field(default=Path(__file__).resolve().parents[2] / "scripts" / "update_printora.sh")
    self_update_windows_script_path: Path = Field(default=Path(__file__).resolve().parents[2] / "scripts" / "update_printora_windows.ps1")
    self_update_timeout_seconds: float = 900.0
    slicer_engine_path: Path | None = None
    slicer_engine_timeout_seconds: float = 600.0
    slicer_engine_work_dir: Path | None = None
    redis_url: str | None = None
    redis_prefix: str = "printora"
    redis_timeout_seconds: float = 0.5
    object_storage_mode: ObjectStorageMode = "local"
    object_storage_endpoint_url: str = ""
    object_storage_region: str = "us-east-1"
    object_storage_access_key: str = ""
    object_storage_secret_key: str = ""
    object_storage_quarantine_bucket: str = "printora-quarantine"
    object_storage_objects_bucket: str = "printora-objects"
    object_storage_artifacts_bucket: str = "printora-artifacts"
    payment_mode: PaymentMode = "disabled"
    payment_webhook_secret: str = ""
    platform_admin_emails: str = "breno@mayder.com.br"
    platform_protection_writes_enabled: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PRINTORA_",
        extra="ignore",
    )

    @property
    def database_path(self) -> Path:
        return self.data_dir / "printora.db"

    @property
    def platform_admin_email_set(self) -> frozenset[str]:
        return parse_platform_admin_emails(self.platform_admin_emails)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _default_data_dir() -> Path:
    if platform.system() == "Darwin":
        return Path.home() / "Library/Application Support/Printora"
    if platform.system() == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Printora"
    return Path.home() / ".local/share/printora"


def parse_platform_admin_emails(value: str) -> frozenset[str]:
    emails = frozenset(item.strip().casefold() for item in value.split(",") if item.strip())
    if any(
        email.count("@") != 1
        or email.startswith("@")
        or email.endswith("@")
        or any(character.isspace() for character in email)
        for email in emails
    ):
        raise ValueError("PRINTORA_PLATFORM_ADMIN_EMAILS contém email inválido")
    return emails
