import asyncio
from types import SimpleNamespace

from fastapi import Request
from fastapi.responses import JSONResponse

from app.rate_limit_middleware import _actor_key, redis_rate_limit_middleware


class FakeRateLimitService:
    configured = True

    def __init__(self, *, allowed: bool, degraded: bool = False) -> None:
        self.decision = SimpleNamespace(
            allowed=allowed,
            degraded=degraded,
            retry_after_seconds=17,
            remaining=9,
        )
        self.calls: list[tuple[str, int, int]] = []

    def rate_limit(self, scope: str, limit: int, window: int):
        self.calls.append((scope, limit, window))
        return self.decision


def _request(
    *,
    path: str = "/api/auth/login",
    method: str = "POST",
    service=None,
    headers: list[tuple[bytes, bytes]] | None = None,
    client: tuple[str, int] | None = ("203.0.113.8", 12345),
) -> Request:
    app = SimpleNamespace(state=SimpleNamespace(recomposable_redis=service))
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": method,
            "scheme": "https",
            "path": path,
            "raw_path": path.encode(),
            "query_string": b"",
            "headers": headers or [],
            "client": client,
            "server": ("printora.test", 443),
            "app": app,
        }
    )


async def _next(_request: Request) -> JSONResponse:
    return JSONResponse({"ok": True})


def test_actor_key_ignores_spoofable_forwarding_and_authorization_headers() -> None:
    first = _request(
        headers=[
            (b"authorization", b"Bearer attacker-one"),
            (b"x-forwarded-for", b"198.51.100.1"),
            (b"cf-connecting-ip", b"198.51.100.2"),
        ]
    )
    second = _request(
        headers=[
            (b"authorization", b"Bearer attacker-two"),
            (b"x-forwarded-for", b"192.0.2.10"),
        ]
    )

    assert _actor_key(first) == _actor_key(second)
    assert _actor_key(_request(client=None)) != _actor_key(first)


def test_rate_limit_bypasses_when_redis_is_not_configured() -> None:
    response = asyncio.run(redis_rate_limit_middleware(_request(service=None), _next))

    assert response.status_code == 200


def test_auth_rate_limit_fails_closed_when_redis_is_degraded() -> None:
    service = FakeRateLimitService(allowed=True, degraded=True)

    response = asyncio.run(
        redis_rate_limit_middleware(_request(service=service), _next)
    )

    assert response.status_code == 503
    assert response.headers["retry-after"] == "5"
    assert service.calls[0][1:] == (20, 60)


def test_rate_limit_denies_exhausted_mutation_and_allows_read() -> None:
    denied = FakeRateLimitService(allowed=False)
    denied_response = asyncio.run(
        redis_rate_limit_middleware(
            _request(path="/api/printers", method="PATCH", service=denied),
            _next,
        )
    )
    allowed = FakeRateLimitService(allowed=True)
    allowed_response = asyncio.run(
        redis_rate_limit_middleware(
            _request(path="/api/printers", method="GET", service=allowed),
            _next,
        )
    )

    assert denied_response.status_code == 429
    assert denied_response.headers["retry-after"] == "17"
    assert denied.calls[0][1:] == (120, 60)
    assert allowed_response.status_code == 200
    assert allowed_response.headers["x-ratelimit-remaining"] == "9"
    assert allowed.calls[0][1:] == (600, 60)


def test_degraded_non_auth_route_continues_without_remaining_header() -> None:
    service = FakeRateLimitService(allowed=True, degraded=True)

    response = asyncio.run(
        redis_rate_limit_middleware(
            _request(path="/api/printers", method="GET", service=service),
            _next,
        )
    )

    assert response.status_code == 200
    assert "x-ratelimit-remaining" not in response.headers
