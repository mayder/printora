from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MayderPrintLab"
    moonraker_url: str = Field(default="http://127.0.0.1:7125")
    data_dir: Path = Field(default=Path.home() / ".local/share/mayderprintlab")
    request_timeout_seconds: float = 5.0

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
