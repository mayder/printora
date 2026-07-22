#!/usr/bin/env python3
"""Cria snapshot SQLite consistente para a transição PostgreSQL."""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


def create_snapshot(source_path: Path, target_path: Path) -> dict[str, object]:
    if target_path.exists():
        raise RuntimeError(f"Destino já existe: {target_path}")
    source = sqlite3.connect(source_path, timeout=60)
    source.execute("PRAGMA busy_timeout=60000")
    try:
        journal_mode = str(source.execute("PRAGMA journal_mode").fetchone()[0]).lower()
        if journal_mode != "wal":
            raise RuntimeError(f"Snapshot online exige WAL; recebido: {journal_mode}")
        source.execute("VACUUM INTO ?", (str(target_path),))
    finally:
        source.close()

    target = sqlite3.connect(f"file:{target_path}?mode=ro", uri=True)
    try:
        integrity = str(target.execute("PRAGMA integrity_check").fetchone()[0])
        if integrity != "ok":
            raise RuntimeError(f"Snapshot falhou na integridade: {integrity}")
        outbox_exists = target.execute(
            """
            SELECT 1
            FROM sqlite_schema
            WHERE type = 'table' AND name = 'postgresql_transition_outbox'
            """
        ).fetchone()
        if outbox_exists is None:
            raise RuntimeError("Snapshot não contém a outbox de transição")
        watermark = int(
            target.execute(
                "SELECT COALESCE(MAX(id), 0) FROM postgresql_transition_outbox"
            ).fetchone()[0]
        )
        schema_revision = int(
            target.execute("SELECT schema_revision FROM app_version WHERE id = 1").fetchone()[0]
        )
        tables = int(
            target.execute(
                """
                SELECT COUNT(*)
                FROM sqlite_schema
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                """
            ).fetchone()[0]
        )
    finally:
        target.close()
    return {
        "integrity": integrity,
        "schema_revision": schema_revision,
        "size_bytes": target_path.stat().st_size,
        "tables": tables,
        "watermark": watermark,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(create_snapshot(args.source, args.target), sort_keys=True))


if __name__ == "__main__":
    main()
