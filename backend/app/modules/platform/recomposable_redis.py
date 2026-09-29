from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import redis
from redis.exceptions import RedisError


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    remaining: int
    retry_after_seconds: int
    degraded: bool = False


class RecomposableRedis:
    def __init__(self, url: str | None, prefix: str = "printora", timeout_seconds: float = 0.5) -> None:
        self.url = url
        self.prefix = prefix.strip(":") or "printora"
        self.timeout_seconds = max(0.1, timeout_seconds)
        self._client = (
            redis.Redis.from_url(
                url,
                decode_responses=True,
                socket_timeout=self.timeout_seconds,
                socket_connect_timeout=self.timeout_seconds,
                health_check_interval=30,
            )
            if url
            else None
        )

    @property
    def configured(self) -> bool:
        return self._client is not None

    def ping(self) -> bool:
        try:
            return bool(self._client and self._client.ping())
        except RedisError:
            return False

    def cache_get(self, namespace: str, key: str) -> Any | None:
        try:
            raw = self._client.get(self._key("cache", namespace, key)) if self._client else None
            return json.loads(raw) if raw is not None else None
        except (RedisError, json.JSONDecodeError):
            return None

    def cache_set(self, namespace: str, key: str, value: Any, ttl_seconds: int) -> bool:
        try:
            return bool(
                self._client
                and self._client.set(
                    self._key("cache", namespace, key),
                    json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
                    ex=max(1, ttl_seconds),
                )
            )
        except (RedisError, TypeError, ValueError):
            return False

    def rate_limit(self, scope: str, limit: int, window_seconds: int) -> RateLimitDecision:
        if not self._client:
            return RateLimitDecision(True, max(0, limit - 1), 0, degraded=True)
        key = self._key("limit", scope)
        try:
            with self._client.pipeline(transaction=True) as pipeline:
                pipeline.incr(key)
                pipeline.ttl(key)
                count, ttl = pipeline.execute()
            if int(count) == 1 or int(ttl) < 0:
                self._client.expire(key, max(1, window_seconds))
                ttl = max(1, window_seconds)
            return RateLimitDecision(
                allowed=int(count) <= max(1, limit),
                remaining=max(0, max(1, limit) - int(count)),
                retry_after_seconds=max(0, int(ttl)),
            )
        except RedisError:
            return RateLimitDecision(True, max(0, limit - 1), 0, degraded=True)

    def set_presence(self, agent_id: int, instance_id: str, ttl_seconds: int = 90) -> bool:
        try:
            return bool(
                self._client
                and self._client.set(
                    self._key("presence", "agent", str(agent_id)),
                    instance_id,
                    ex=max(5, ttl_seconds),
                )
            )
        except RedisError:
            return False

    def publish(self, channel: str, payload: dict[str, Any]) -> bool:
        try:
            if not self._client:
                return False
            self._client.publish(
                self.channel_name(channel),
                json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            )
            return True
        except (RedisError, TypeError, ValueError):
            return False

    def channel_name(self, channel: str) -> str:
        return self._key("pubsub", channel)

    def _key(self, *parts: str) -> str:
        cleaned = [part.replace(":", "_")[:160] for part in parts]
        return ":".join((self.prefix, *cleaned))
