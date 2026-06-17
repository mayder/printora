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

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="PRINTORA_",
        extra="ignore",
    )

    @property
    def database_path(self) -> Path:
        return self.data_dir / "printora.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _default_data_dir() -> Path:
    if platform.system() == "Darwin":
        return Path.home() / "Library/Application Support/Printora"
    if platform.system() == "Windows":
        return Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local")) / "Printora"
    return Path.home() / ".local/share/printora"
