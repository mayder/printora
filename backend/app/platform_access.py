from __future__ import annotations

from app.config import Settings, get_settings


def is_platform_admin(email: str, settings: Settings | None = None) -> bool:
    configured = settings or get_settings()
    return email.strip().casefold() in configured.platform_admin_email_set
