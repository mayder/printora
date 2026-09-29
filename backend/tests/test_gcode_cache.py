from pathlib import Path

import pytest
from fastapi import HTTPException

from app.agent_pairing import AgentPairingRepository
from app.config import Settings
from app.database import connect_database, initialize_database
from app.gcode_cache import (
    gcode_cache_key,
    resolve_gcode_cache_upload_filename,
)
from app.modules.operations.contracts import AgentJobCreateRequest
from app.printers import PrinterRepository


def _seed_agent(settings: Settings):
    initialize_database(settings.database_path)
    with connect_database(settings.database_path) as connection:
        printer_id = int(
            connection.execute(
                "INSERT INTO printers (name, moonraker_url) VALUES (?, ?)",
                ("Voron Unicode", "http://127.0.0.1:7125"),
            ).lastrowid
        )
        connection.execute(
            """
            INSERT INTO printer_agents (
                printer_id, stable_id, credential_hash, credential_prefix,
                agent_version, platform, status, last_seen_at
            ) VALUES (?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
            """,
            (
                printer_id,
                "agent-unicode",
                "hash-unicode",
                "prefix-unicode",
                "0.1.36",
                "linux-arm64",
            ),
        )
    printer = PrinterRepository(settings.database_path).get_printer(printer_id)
    agent = AgentPairingRepository(settings.database_path).latest_active_agent(printer_id)
    assert printer is not None
    assert agent is not None
    return printer, agent


def test_cache_upload_recovers_canonical_unicode_filename_from_active_job(
    tmp_path: Path,
) -> None:
    settings = Settings(data_dir=tmp_path)
    printer, agent = _seed_agent(settings)
    filename = "跳舞_PLA_23m3s.gcode"
    cache_key = gcode_cache_key(printer.id, filename)
    AgentPairingRepository(settings.database_path).create_job(
        printer,
        AgentJobCreateRequest(
            job_type="remote_gcode_cache",
            agent_id=agent.id,
            correlation_id="unicode-cache-001",
            payload={
                "filename": filename,
                "cache_key": cache_key,
                "max_bytes": 96 * 1024 * 1024,
            },
        ),
    )

    resolved = resolve_gcode_cache_upload_filename(
        settings,
        agent,
        cache_key,
        "??_PLA_23m3s.gcode",
    )

    assert resolved == filename


def test_cache_upload_rejects_key_without_matching_active_job(tmp_path: Path) -> None:
    settings = Settings(data_dir=tmp_path)
    printer, agent = _seed_agent(settings)
    cache_key = gcode_cache_key(printer.id, "outro.gcode")

    with pytest.raises(HTTPException) as exc_info:
        resolve_gcode_cache_upload_filename(
            settings,
            agent,
            cache_key,
            "arquivo-incorreto.gcode",
        )

    assert exc_info.value.status_code == 409
