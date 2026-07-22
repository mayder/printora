import asyncio

from app.agent_channel import AgentWebSocketManager
from app.agent_pairing import AgentRecord


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
