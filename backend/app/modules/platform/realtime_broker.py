from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Any

import redis.asyncio as async_redis
from redis.exceptions import RedisError

from app.modules.platform.recomposable_redis import RecomposableRedis


NotificationHandler = Callable[[dict[str, Any]], Awaitable[None]]


class RealtimeBroker:
    def __init__(
        self,
        redis_service: RecomposableRedis,
        handler: NotificationHandler,
        channel: str = "agent",
    ) -> None:
        self.redis_service = redis_service
        self.handler = handler
        self.channel = channel
        self._client: async_redis.Redis | None = None
        self._task: asyncio.Task[None] | None = None
        self._stopping = asyncio.Event()

    async def start(self) -> bool:
        if not self.redis_service.url or self._task is not None:
            return False
        self._client = async_redis.Redis.from_url(
            self.redis_service.url,
            decode_responses=True,
            socket_timeout=self.redis_service.timeout_seconds,
            socket_connect_timeout=self.redis_service.timeout_seconds,
            health_check_interval=30,
        )
        try:
            await self._client.ping()
        except RedisError:
            await self._client.aclose()
            self._client = None
            return False
        self._stopping.clear()
        self._task = asyncio.create_task(self._listen(), name="printora-realtime-broker")
        return True

    async def stop(self) -> None:
        self._stopping.set()
        task = self._task
        self._task = None
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _listen(self) -> None:
        assert self._client is not None
        pubsub = self._client.pubsub(ignore_subscribe_messages=True)
        await pubsub.subscribe(self.redis_service.channel_name(self.channel))
        try:
            while not self._stopping.is_set():
                message = await pubsub.get_message(timeout=1.0)
                if not message or message.get("type") != "message":
                    continue
                try:
                    payload = json.loads(str(message.get("data") or "{}"))
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    await self.handler(payload)
        except RedisError:
            return
        finally:
            await pubsub.aclose()
