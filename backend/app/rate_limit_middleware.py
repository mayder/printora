from __future__ import annotations

import asyncio
import hashlib

from fastapi import Request
from fastapi.responses import JSONResponse


AUTH_PATHS = {
    "/api/auth/register",
    "/api/auth/login",
    "/api/auth/login/mfa",
    "/api/auth/step-up",
    "/api/agent/pairing/exchange",
}


async def redis_rate_limit_middleware(request: Request, call_next):
    service = getattr(request.app.state, "recomposable_redis", None)
    if service is None or not service.configured:
        return await call_next(request)
    actor = _actor_key(request)
    if request.url.path in AUTH_PATHS:
        limit, window = 20, 60
    elif request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}:
        limit, window = 120, 60
    else:
        limit, window = 600, 60
    scope = f"http:{actor}:{request.method.upper()}:{request.url.path}"
    decision = await asyncio.to_thread(service.rate_limit, scope, limit, window)
    if decision.degraded and request.url.path in AUTH_PATHS:
        return JSONResponse(
            status_code=503,
            headers={"Retry-After": "5"},
            content={"detail": "proteção contra abuso temporariamente indisponível"},
        )
    if not decision.allowed:
        return JSONResponse(
            status_code=429,
            headers={"Retry-After": str(decision.retry_after_seconds)},
            content={"detail": "limite de requisições atingido"},
        )
    response = await call_next(request)
    if not decision.degraded:
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
    return response


def _actor_key(request: Request) -> str:
    # Forwarding and Authorization headers are attacker-controlled at this
    # boundary. Use the peer resolved by the ASGI server/proxy configuration.
    source = request.client.host if request.client else "anonymous"
    return hashlib.sha256(source.encode("utf-8")).hexdigest()[:24]
