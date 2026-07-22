from __future__ import annotations

import os


POSTGRESQL_PREFIXES = ("postgresql://", "postgresql+psycopg://")


def configured_database_url() -> str | None:
    value = os.environ.get("PRINTORA_DATABASE_URL", "").strip()
    return value or None


def uses_postgresql() -> bool:
    value = configured_database_url()
    return bool(value and value.startswith(POSTGRESQL_PREFIXES))


def require_postgresql_url() -> str:
    value = configured_database_url()
    if not value or not value.startswith(POSTGRESQL_PREFIXES):
        raise RuntimeError("PRINTORA_DATABASE_URL PostgreSQL não configurada")
    return value.replace("postgresql+psycopg://", "postgresql://", 1)
