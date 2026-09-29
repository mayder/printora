from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse, Response

from app.config import get_settings
from app.modules.platform.idempotency import (
    IdempotencyRepository,
    idempotency_scope,
    request_fingerprint,
)


MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
MAX_CACHED_RESPONSE_BYTES = 512 * 1024


async def idempotency_middleware(request: Request, call_next):
    key = request.headers.get("idempotency-key", "").strip()
    if request.method.upper() not in MUTATING_METHODS or not key:
        return await call_next(request)
    body = await request.body()
    scope = idempotency_scope(request.method, request.url.path, request.headers.get("authorization"))
    fingerprint = request_fingerprint(
        request.method,
        request.url.path,
        request.url.query,
        body,
        request.headers.get("content-type", ""),
    )
    repository = IdempotencyRepository(get_settings().database_path)
    try:
        decision = repository.begin(scope, key, fingerprint)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})
    if decision.status == "conflict":
        return JSONResponse(status_code=409, content={"detail": "Idempotency-Key já usada com outra requisição"})
    if decision.status == "processing":
        return JSONResponse(status_code=409, headers={"Retry-After": "2"}, content={"detail": "requisição idempotente em processamento"})
    if decision.status == "replay":
        headers = dict(decision.response_headers or {})
        headers["Idempotency-Status"] = "replayed"
        return Response(content=decision.response_body or b"", status_code=decision.response_status or 200, headers=headers)
    lock_token = decision.lock_token or ""
    try:
        response = await call_next(request)
        response_body = b"".join([chunk async for chunk in response.body_iterator])
    except Exception:
        repository.fail(scope, key, lock_token)
        raise
    headers = {
        name: value
        for name, value in response.headers.items()
        if name.lower() in {"content-type", "location", "etag"}
    }
    if response.status_code < 500 and len(response_body) <= MAX_CACHED_RESPONSE_BYTES:
        repository.complete(scope, key, lock_token, response.status_code, headers, response_body)
        status = "stored"
    else:
        repository.fail(scope, key, lock_token)
        status = "not-stored"
    headers = dict(response.headers)
    headers["Idempotency-Status"] = status
    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type,
        background=response.background,
    )
