from pathlib import Path

from app.agent_pairing import AgentPairingRepository
from app.database import connect_database, initialize_database
from app.modules.operations.contracts import AgentHeartbeatRequest, AgentJobCreateRequest
from app.printers import PrinterRepository


def test_coalesced_read_job_reuses_only_same_active_scope(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        printer_id = int(
            connection.execute(
                """
                INSERT INTO printers (name, moonraker_url, host_audit_mode)
                VALUES (?, ?, 'disabled')
                """,
                ("Voron Coalescence", "http://127.0.0.1:7125"),
            ).lastrowid
        )
        agent_id = int(
            connection.execute(
                """
                INSERT INTO printer_agents (
                    printer_id, stable_id, credential_hash, credential_prefix,
                    agent_version, platform, status, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
                """,
                (
                    printer_id,
                    "agent-coalescence",
                    "hash-coalescence",
                    "prefix-coalescence",
                    "0.1.34",
                    "linux-arm64",
                ),
            ).lastrowid
        )

    printer = PrinterRepository(database_path).get_printer(printer_id)
    assert printer is not None
    repository = AgentPairingRepository(database_path)
    first_request = AgentJobCreateRequest(
        job_type="remote_operation_status",
        agent_id=agent_id,
        correlation_id="operation-read-001",
        payload={"include": ["status"]},
    )
    same_scope_request = AgentJobCreateRequest(
        job_type="remote_operation_status",
        agent_id=agent_id,
        correlation_id="operation-read-002",
        payload={"include": ["status"]},
    )
    different_payload_request = AgentJobCreateRequest(
        job_type="remote_operation_status",
        agent_id=agent_id,
        correlation_id="operation-read-003",
        payload={"include": ["status", "files"]},
    )

    first = repository.create_or_reuse_job(printer, first_request)
    reused = repository.create_or_reuse_job(printer, same_scope_request)
    different = repository.create_or_reuse_job(printer, different_payload_request)

    assert reused.id == first.id
    assert reused.correlation_id == first.correlation_id
    assert different.id != first.id

    with connect_database(database_path) as connection:
        connection.execute(
            "UPDATE agent_jobs SET payload_json = ? WHERE id = ?",
            ("{invalid", first.id),
        )
    after_malformed_legacy_payload = repository.create_or_reuse_job(
        printer,
        AgentJobCreateRequest(
            job_type="remote_operation_status",
            agent_id=agent_id,
            correlation_id="operation-read-004",
            payload={"include": ["status"]},
        ),
    )
    assert after_malformed_legacy_payload.id not in {first.id, different.id}


def test_regular_job_creation_never_coalesces_mutations(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    with connect_database(database_path) as connection:
        printer_id = int(
            connection.execute(
                """
                INSERT INTO printers (name, moonraker_url, host_audit_mode)
                VALUES (?, ?, 'disabled')
                """,
                ("Voron Mutation", "http://127.0.0.1:7125"),
            ).lastrowid
        )
        agent_id = int(
            connection.execute(
                """
                INSERT INTO printer_agents (
                    printer_id, stable_id, credential_hash, credential_prefix,
                    agent_version, platform, status, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, 'active', CURRENT_TIMESTAMP)
                """,
                (
                    printer_id,
                    "agent-mutation",
                    "hash-mutation",
                    "prefix-mutation",
                    "0.1.34",
                    "linux-arm64",
                ),
            ).lastrowid
        )

    printer = PrinterRepository(database_path).get_printer(printer_id)
    assert printer is not None
    repository = AgentPairingRepository(database_path)
    first = repository.create_job(
        printer,
        AgentJobCreateRequest(
            job_type="remote_gcode_execute",
            agent_id=agent_id,
            correlation_id="mutation-001",
            payload={"script": "SAFE_FIXTURE"},
        ),
    )
    second = repository.create_job(
        printer,
        AgentJobCreateRequest(
            job_type="remote_gcode_execute",
            agent_id=agent_id,
            correlation_id="mutation-002",
            payload={"script": "SAFE_FIXTURE"},
        ),
    )

    assert second.id != first.id

    agent = repository.latest_active_agent(printer_id)
    assert agent is not None
    first_ack = repository.ack_job(agent, first.id)
    second_ack = repository.ack_job(agent, second.id)
    assert first_ack is not None and first_ack.status == "in_progress"
    assert second_ack is not None and second_ack.status == "in_progress"
    old_timestamp = "2000-01-01 00:00:00"
    with connect_database(database_path) as connection:
        connection.execute(
            "UPDATE agent_jobs SET updated_at = ? WHERE id IN (?, ?)",
            (old_timestamp, first.id, second.id),
        )

    repository.heartbeat(agent, AgentHeartbeatRequest())

    with connect_database(database_path) as connection:
        rows = connection.execute(
            "SELECT id, updated_at FROM agent_jobs WHERE id IN (?, ?) ORDER BY id",
            (first.id, second.id),
        ).fetchall()
    assert rows[0]["updated_at"] != old_timestamp
    assert rows[1]["updated_at"] == old_timestamp
