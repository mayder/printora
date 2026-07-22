from app.modules.platform.recomposable_redis import RecomposableRedis


class FakePipeline:
    def __init__(self, client) -> None:
        self.client = client

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None

    def incr(self, key: str) -> None:
        self.client.values[key] = int(self.client.values.get(key, 0)) + 1

    def ttl(self, key: str) -> None:
        self.key = key

    def execute(self):
        return [self.client.values[self.key], self.client.ttls.get(self.key, -1)]


class FakeRedis:
    def __init__(self) -> None:
        self.values: dict[str, object] = {}
        self.ttls: dict[str, int] = {}
        self.messages: list[tuple[str, str]] = []

    def ping(self) -> bool:
        return True

    def get(self, key: str):
        return self.values.get(key)

    def set(self, key: str, value, ex: int) -> bool:
        self.values[key] = value
        self.ttls[key] = ex
        return True

    def expire(self, key: str, seconds: int) -> None:
        self.ttls[key] = seconds

    def pipeline(self, transaction: bool):
        assert transaction is True
        return FakePipeline(self)

    def publish(self, channel: str, payload: str) -> int:
        self.messages.append((channel, payload))
        return 1


def test_unavailable_redis_degrades_without_blocking_canonical_flow() -> None:
    service = RecomposableRedis(None)

    assert service.cache_get("catalog", "key") is None
    assert service.cache_set("catalog", "key", {"value": 1}, 30) is False
    assert service.rate_limit("actor", 10, 60).degraded is True
    assert service.publish("agent", {"job_id": 7}) is False


def test_cache_rate_limit_presence_and_pubsub_are_namespaced() -> None:
    service = RecomposableRedis(None, prefix="printora")
    fake = FakeRedis()
    service._client = fake

    assert service.cache_set("catalog", "voron", {"items": 2}, 30) is True
    assert service.cache_get("catalog", "voron") == {"items": 2}
    assert service.rate_limit("user-1", 1, 60).allowed is True
    blocked = service.rate_limit("user-1", 1, 60)
    assert blocked.allowed is False
    assert service.set_presence(7, "blue:123", 90) is True
    assert service.publish("agent", {"job_id": 9}) is True
    assert all(key.startswith("printora:") for key in fake.values)
    assert fake.messages[0][0] == "printora:pubsub:agent"
