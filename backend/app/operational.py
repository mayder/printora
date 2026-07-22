from __future__ import annotations

import json
import logging
import os
import sys
import time
from collections import defaultdict
from threading import Lock
from uuid import uuid4

from fastapi import Request, Response

from app.config import Settings
from app.database import connect_database


LOGGER = logging.getLogger("printora.http")
if not LOGGER.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False
REQUEST_ID_HEADER = "X-Request-ID"
MAX_REQUEST_ID_LENGTH = 128


class HttpMetrics:
    def __init__(self) -> None:
        self._lock = Lock()
        self._requests: dict[tuple[str, str, int], int] = defaultdict(int)
        self._duration_seconds = 0.0

    def observe(self, method: str, route: str, status_code: int, duration_seconds: float) -> None:
        with self._lock:
            self._requests[(method, route, status_code)] += 1
            self._duration_seconds += duration_seconds

    def render(self) -> str:
        with self._lock:
            rows = sorted(self._requests.items())
            duration_seconds = self._duration_seconds
        lines = [
            "# HELP printora_http_requests_total Total de requests HTTP.",
            "# TYPE printora_http_requests_total counter",
        ]
        for (method, route, status_code), count in rows:
            lines.append(
                'printora_http_requests_total{method="%s",route="%s",status="%d"} %d'
                % (_label(method), _label(route), status_code, count)
            )
        lines.extend(
            [
                "# HELP printora_http_request_duration_seconds_total Tempo HTTP acumulado.",
                "# TYPE printora_http_request_duration_seconds_total counter",
                f"printora_http_request_duration_seconds_total {duration_seconds:.6f}",
            ]
        )
        return "\n".join(lines) + "\n"


http_metrics = HttpMetrics()


async def request_observability_middleware(request: Request, call_next) -> Response:
    request_id = _request_id(request.headers.get(REQUEST_ID_HEADER))
    request.state.request_id = request_id
    started_at = time.monotonic()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration_seconds = time.monotonic() - started_at
        route = _route_template(request)
        http_metrics.observe(request.method, route, status_code, duration_seconds)
        LOGGER.info(
            json.dumps(
                {
                    "event": "http_request_completed",
                    "request_id": request_id,
                    "method": request.method,
                    "route": route,
                    "status_code": status_code,
                    "duration_ms": round(duration_seconds * 1000, 3),
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        if "response" in locals():
            response.headers[REQUEST_ID_HEADER] = request_id


def readiness(settings: Settings) -> tuple[bool, dict[str, object]]:
    if not settings.data_dir.is_dir() or not os.access(settings.data_dir, os.W_OK):
        return False, {"status": "not_ready", "database": "data_dir_not_writable"}
    try:
        with connect_database(settings.database_path) as connection:
            connection.execute("SELECT 1").fetchone()
            schema = connection.execute(
                "SELECT schema_revision FROM app_version WHERE id = 1"
            ).fetchone()
    except Exception as exc:
        return False, {"status": "not_ready", "database": "unavailable", "reason": type(exc).__name__}
    if schema is None:
        return False, {"status": "not_ready", "database": "schema_missing"}
    return True, {"status": "ready", "database": "ok", "schema_revision": int(schema["schema_revision"])}


def _request_id(candidate: str | None) -> str:
    if candidate and 0 < len(candidate) <= MAX_REQUEST_ID_LENGTH:
        if all(character.isalnum() or character in "-_.:" for character in candidate):
            return candidate
    return uuid4().hex


def _route_template(request: Request) -> str:
    route = request.scope.get("route")
    path = getattr(route, "path", None)
    return str(path or request.url.path)[:240]


def _label(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "")
