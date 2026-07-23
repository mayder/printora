from __future__ import annotations

import asyncio
import os
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from app.agent_pairing import AGENT_PROTOCOL_VERSION, AgentJobRecord, AgentRecord
from app.database import connect_database
from app.modules.platform.recomposable_redis import RecomposableRedis


class AgentWebSocketSession:
    def __init__(self, agent: AgentRecord, websocket, session_id: str) -> None:
        self.agent = agent
        self.websocket = websocket
        self.session_id = session_id
        self.send_lock = asyncio.Lock()


class AgentWebSocketManager:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._sessions: dict[int, AgentWebSocketSession] = {}
        self._database_path: Path | None = None
        self._redis: RecomposableRedis | None = None
        self._instance_id = f"{socket.gethostname()}:{os.getpid()}"

    def configure(
        self,
        database_path: Path,
        redis_service: RecomposableRedis,
        instance_id: str | None = None,
    ) -> None:
        self._database_path = database_path
        self._redis = redis_service
        if instance_id:
            self._instance_id = instance_id

    async def register(self, agent: AgentRecord, websocket) -> None:
        session = AgentWebSocketSession(agent, websocket, uuid4().hex)
        async with self._lock:
            previous = self._sessions.get(agent.id)
            self._sessions[agent.id] = session
        await asyncio.to_thread(self._persist_session, session)
        if self._redis is not None:
            await asyncio.to_thread(
                self._redis.publish,
                "agent",
                {"type": "session_replaced", "agent_id": agent.id, "session_id": session.session_id},
            )
        if previous is not None and previous.websocket is not websocket:
            try:
                await previous.websocket.close(code=1012, reason="replaced_by_reconnect")
            except Exception:
                pass

    async def unregister(self, agent_id: int, websocket=None) -> None:
        async with self._lock:
            current = self._sessions.get(agent_id)
            if current is None or (websocket is not None and current.websocket is not websocket):
                current = None
        if current is not None:
            await asyncio.to_thread(self._disconnect_session, current.session_id)
            async with self._lock:
                if self._sessions.get(agent_id) is current:
                    self._sessions.pop(agent_id, None)

    async def disconnect_all(self) -> None:
        async with self._lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        if sessions:
            await asyncio.gather(
                *(asyncio.to_thread(self._disconnect_session, session.session_id) for session in sessions)
            )

    async def send(self, agent_id: int, message: dict) -> bool:
        async with self._lock:
            session = self._sessions.get(agent_id)
        if session is None:
            return False
        if self._database_path is not None and not await asyncio.to_thread(self._is_session_active, session.session_id):
            await self.unregister(session.agent.id, session.websocket)
            return False
        try:
            async with session.send_lock:
                await session.websocket.send_json(message)
            return True
        except Exception:
            await self.unregister(agent_id, session.websocket)
            return False

    async def push_local_job(self, job: AgentJobRecord) -> bool:
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
        if self._database_path is not None and not await asyncio.to_thread(self._is_session_active, session.session_id):
            await self.unregister(session.agent.id, session.websocket)
            return False
        try:
            async with session.send_lock:
                await session.websocket.send_json(job_message(job))
            return True
        except Exception:
            await self.unregister(session.agent.id, session.websocket)
            return False

    async def heartbeat(self, agent_id: int, websocket, last_job_id: int | None = None) -> None:
        async with self._lock:
            session = self._sessions.get(agent_id)
        if session is None or session.websocket is not websocket:
            return
        await asyncio.to_thread(self._touch_session, session, last_job_id)

    async def handle_notification(self, payload: dict) -> None:
        if payload.get("type") == "session_replaced":
            agent_id = int(payload.get("agent_id") or 0)
            async with self._lock:
                session = self._sessions.get(agent_id)
            if session is not None and session.session_id != payload.get("session_id"):
                try:
                    await session.websocket.close(code=1012, reason="replaced_by_reconnect")
                finally:
                    await self.unregister(agent_id, session.websocket)
            return
        if payload.get("type") != "job_available" or self._database_path is None:
            return
        job_id = int(payload.get("agent_job_id") or 0)
        printer_id = int(payload.get("printer_id") or 0)
        if not job_id or not printer_id:
            return
        from app.agent_pairing import AgentPairingRepository

        job = await asyncio.to_thread(AgentPairingRepository(self._database_path).get_job, printer_id, job_id)
        if job is not None:
            await self.push_local_job(job)

    def _persist_session(self, session: AgentWebSocketSession) -> None:
        if self._database_path is None:
            return
        now = _timestamp(_utc_now())
        expires_at = _timestamp(_utc_now() + timedelta(seconds=90))
        with connect_database(self._database_path) as connection:
            connection.execute(
                """
                UPDATE realtime_sessions
                SET disconnected_at = ?, expires_at = ?
                WHERE agent_id = ? AND disconnected_at IS NULL
                """,
                (now, now, session.agent.id),
            )
            connection.execute(
                """
                INSERT INTO realtime_sessions (
                    session_id, agent_id, printer_id, instance_id, protocol_version,
                    connected_at, heartbeat_at, expires_at, disconnected_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    session.session_id,
                    session.agent.id,
                    session.agent.printer_id,
                    self._instance_id,
                    AGENT_PROTOCOL_VERSION,
                    now,
                    now,
                    expires_at,
                ),
            )
        if self._redis is not None:
            self._redis.set_presence(session.agent.id, self._instance_id, 90)

    def _is_session_active(self, session_id: str) -> bool:
        if self._database_path is None:
            return True
        with connect_database(self._database_path) as connection:
            row = connection.execute(
                """
                SELECT session_id FROM realtime_sessions
                WHERE session_id = ? AND disconnected_at IS NULL AND expires_at > ?
                """,
                (session_id, _timestamp(_utc_now())),
            ).fetchone()
        return row is not None

    def _touch_session(self, session: AgentWebSocketSession, last_job_id: int | None) -> None:
        if self._database_path is None:
            return
        now = _utc_now()
        with connect_database(self._database_path) as connection:
            connection.execute(
                """
                UPDATE realtime_sessions
                SET heartbeat_at = ?, expires_at = ?,
                    last_acknowledged_job_id = COALESCE(?, last_acknowledged_job_id)
                WHERE session_id = ? AND disconnected_at IS NULL
                """,
                (_timestamp(now), _timestamp(now + timedelta(seconds=90)), last_job_id, session.session_id),
            )
        if self._redis is not None:
            self._redis.set_presence(session.agent.id, self._instance_id, 90)

    def _disconnect_session(self, session_id: str) -> None:
        if self._database_path is None:
            return
        with connect_database(self._database_path) as connection:
            connection.execute(
                "UPDATE realtime_sessions SET disconnected_at = ?, expires_at = ? WHERE session_id = ? AND disconnected_at IS NULL",
                (_timestamp(_utc_now()), _timestamp(_utc_now()), session_id),
            )


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


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")
