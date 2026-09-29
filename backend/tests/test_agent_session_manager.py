import asyncio
from pathlib import Path

from app.agent_channel import AgentWebSocketManager
from app.auth import AuthRepository, UserRegisterRequest
from app.database import connect_database, initialize_database
from app.agent_pairing import AgentRecord
from app.modules.platform.recomposable_redis import RecomposableRedis
from app.printers import PrinterCreate, PrinterRepository


class FakeWebSocket:
    def __init__(self) -> None:
        self.closed = False
        self.messages: list[dict] = []

    async def close(self, **_kwargs) -> None:
        self.closed = True

    async def send_json(self, message: dict) -> None:
        self.messages.append(message)


def test_reconnect_replaces_old_session_without_old_disconnect_removing_new() -> None:
    asyncio.run(_assert_reconnect_replaces_old_session())


async def _assert_reconnect_replaces_old_session() -> None:
    manager = AgentWebSocketManager()
    agent = AgentRecord(
        id=7,
        printer_id=3,
        stable_id="agent-session-7",
        agent_version="0.1.33",
        platform="linux/arm64",
        status="active",
        paired_at="2026-07-22 00:00:00",
        last_seen_at="2026-07-22 00:00:00",
        revoked_at=None,
        rotated_at=None,
        capabilities={},
        credential_prefix="[redacted]",
    )
    old = FakeWebSocket()
    new = FakeWebSocket()

    await manager.register(agent, old)
    await manager.register(agent, new)
    await manager.unregister(agent.id, old)

    assert old.closed is True
    assert await manager.send(agent.id, {"message_type": "ack"}) is True
    assert new.messages == [{"message_type": "ack"}]


def test_database_fences_session_owned_by_another_instance(tmp_path: Path) -> None:
    asyncio.run(_assert_database_fences_session(tmp_path))


async def _assert_database_fences_session(tmp_path: Path) -> None:
    database_path = tmp_path / "printora.db"
    initialize_database(database_path)
    user = AuthRepository(database_path).create_user(
        UserRegisterRequest(email="session-fence@example.com", password="correct-horse")
    )
    printer = PrinterRepository(database_path, user_id=user.id).create_printer(
        PrinterCreate(name="Voron session", moonraker_url="http://127.0.0.1:7125", host_audit_mode="disabled")
    )
    with connect_database(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO printer_agents (
                printer_id, owner_user_id, stable_id, credential_hash, credential_prefix,
                agent_version, platform, capabilities_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, '{}', 'active')
            """,
            (printer.id, user.id, "agent-fenced", "hash-fenced", "[redacted]", "0.1.33", "linux/arm64"),
        )
        agent_id = int(cursor.lastrowid)
    agent = AgentRecord(
        id=agent_id,
        printer_id=printer.id,
        stable_id="agent-fenced",
        agent_version="0.1.33",
        platform="linux/arm64",
        status="active",
        paired_at="2026-07-22 00:00:00",
        last_seen_at=None,
        revoked_at=None,
        rotated_at=None,
        capabilities={},
        credential_prefix="[redacted]",
    )
    first = AgentWebSocketManager()
    second = AgentWebSocketManager()
    first.configure(database_path, RecomposableRedis(None), "blue:100")
    second.configure(database_path, RecomposableRedis(None), "green:200")
    old_socket = FakeWebSocket()
    new_socket = FakeWebSocket()

    await first.register(agent, old_socket)
    await second.register(agent, new_socket)

    assert await first.send(agent.id, {"message_type": "stale"}) is False
    assert await second.send(agent.id, {"message_type": "current"}) is True
    with connect_database(database_path) as connection:
        active = connection.execute(
            "SELECT instance_id FROM realtime_sessions WHERE agent_id = ? AND disconnected_at IS NULL",
            (agent.id,),
        ).fetchall()
    assert [row["instance_id"] for row in active] == ["green:200"]
