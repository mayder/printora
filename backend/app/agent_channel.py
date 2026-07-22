from __future__ import annotations

import asyncio

from app.agent_pairing import AGENT_PROTOCOL_VERSION, AgentJobRecord, AgentRecord


class AgentWebSocketSession:
    def __init__(self, agent: AgentRecord, websocket) -> None:
        self.agent = agent
        self.websocket = websocket
        self.send_lock = asyncio.Lock()


class AgentWebSocketManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._sessions: dict[int, AgentWebSocketSession] = {}

    async def register(self, agent: AgentRecord, websocket) -> None:
        async with self._lock:
            previous = self._sessions.get(agent.id)
            self._sessions[agent.id] = AgentWebSocketSession(agent, websocket)
        if previous is not None and previous.websocket is not websocket:
            try:
                await previous.websocket.close(code=1012, reason="replaced_by_reconnect")
            except Exception:
                pass

    async def unregister(self, agent_id: int, websocket=None) -> None:
        async with self._lock:
            current = self._sessions.get(agent_id)
            if current is not None and (websocket is None or current.websocket is websocket):
                self._sessions.pop(agent_id, None)

    async def send(self, agent_id: int, message: dict) -> bool:
        async with self._lock:
            session = self._sessions.get(agent_id)
        if session is None:
            return False
        try:
            async with session.send_lock:
                await session.websocket.send_json(message)
            return True
        except Exception:
            await self.unregister(agent_id, session.websocket)
            return False

    async def push_job(self, job: AgentJobRecord) -> bool:
        async with self._lock:
            if job.agent_id is not None:
                session = self._sessions.get(job.agent_id)
            else:
                session = next(
                    (candidate for candidate in self._sessions.values() if candidate.agent.printer_id == job.printer_id),
                    None,
                )
        if session is None:
            return False
        try:
            async with session.send_lock:
                await session.websocket.send_json(job_message(job))
            return True
        except Exception:
            await self.unregister(session.agent.id, session.websocket)
            return False


agent_ws_manager = AgentWebSocketManager()


def protocol_message(message_type: str, payload: dict, correlation_id: str | None = None) -> dict:
    return {
        "protocol_version": AGENT_PROTOCOL_VERSION,
        "message_type": message_type,
        "correlation_id": correlation_id or "server",
        "payload": payload,
    }


def job_message(job: AgentJobRecord) -> dict:
    return protocol_message(
        "job",
        {
            "job_id": job.id,
            "correlation_id": job.correlation_id,
            "job_type": job.job_type,
            "payload": job.payload,
            "attempts": job.attempts,
        },
        job.correlation_id,
    )
