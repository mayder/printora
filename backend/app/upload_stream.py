from __future__ import annotations

from starlette.requests import Request


async def read_limited_upload(request: Request, max_bytes: int) -> bytes:
    if max_bytes <= 0:
        raise ValueError("limite de upload inválido")
    declared_length = request.headers.get("content-length")
    if declared_length:
        try:
            if int(declared_length) > max_bytes:
                raise ValueError(f"arquivo excede limite de {max_bytes // (1024 * 1024)} MB")
        except ValueError as exc:
            if "excede limite" in str(exc):
                raise
            raise ValueError("Content-Length inválido") from exc
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > max_bytes:
            raise ValueError(f"arquivo excede limite de {max_bytes // (1024 * 1024)} MB")
        body.extend(chunk)
    if not body:
        raise ValueError("arquivo vazio")
    return bytes(body)
