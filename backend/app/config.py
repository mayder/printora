from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

HostAuditMode = Literal["disabled", "local", "ssh"]
FirmwareBuildMode = Literal["disabled", "local"]


class Settings(BaseSettings):
    app_name: str = "MayderPrintLab"
    moonraker_url: str = Field(default="http://127.0.0.1:7125")
    data_dir: Path = Field(default=Path.home() / ".local/share/mayderprintlab")
    frontend_dist_dir: Path = Field(default=Path(__file__).resolve().parents[2] / "frontend" / "dist")
    request_timeout_seconds: float = 5.0
    host_audit_mode: HostAuditMode = "disabled"
    host_audit_ssh_target: str = "pi@voron.local"
    host_audit_timeout_seconds: float = 12.0
    firmware_build_mode: FirmwareBuildMode = "disabled"
    firmware_build_timeout_seconds: float = 900.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="MAYDER_PRINT_LAB_",
        extra="ignore",
    )

    @property
    def database_path(self) -> Path:
        return self.data_dir / "mayderprintlab.db"


@lru_cache
def get_settings() -> Settings:
    return Settings()
