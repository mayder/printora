#!/usr/bin/env python3
"""Exporta snapshots determinísticos dos contratos HTTP e realtime públicos."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
HTTP_CONTRACT = ROOT / "docs" / "contracts" / "http-v1.openapi.json"
REALTIME_CONTRACT = ROOT / "docs" / "contracts" / "realtime-v1.json"


def load_contracts() -> tuple[dict[str, Any], dict[str, Any]]:
    sys.path.insert(0, str(BACKEND))
    from fastapi.routing import APIWebSocketRoute

    from app.agent_pairing import (
        AgentEventRecord,
        AgentHeartbeatRequest,
        AgentHeartbeatResponse,
        AgentJobErrorRequest,
        AgentJobRecord,
        AgentJobResultRequest,
        AgentProtocolMessage,
        AgentSnapshotRequest,
    )
    from app.main import app

    openapi = app.openapi()
    openapi["info"]["x-contract-version"] = "1.0.0"
    openapi["info"]["x-compatible-with"] = ["1.x"]
    websocket_routes = sorted(
        (
            {"path": route.path, "name": route.name}
            for route in app.routes
            if isinstance(route, APIWebSocketRoute)
        ),
        key=lambda item: (item["path"], item["name"]),
    )
    protocol_models = (
        AgentProtocolMessage,
        AgentHeartbeatRequest,
        AgentHeartbeatResponse,
        AgentSnapshotRequest,
        AgentJobRecord,
        AgentJobResultRequest,
        AgentJobErrorRequest,
        AgentEventRecord,
    )
    realtime = {
        "contract_version": "1.0.0",
        "compatible_with": ["1.x"],
        "websockets": websocket_routes,
        "schemas": {
            model.__name__: model.model_json_schema(mode="validation")
            for model in protocol_models
        },
    }
    return openapi, realtime


def serialize(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def write_or_check(path: Path, content: str, check: bool) -> None:
    if check:
        if not path.is_file() or path.read_text(encoding="utf-8") != content:
            raise SystemExit(
                f"contrato divergente: revise compatibilidade e execute "
                f"{Path(__file__).relative_to(ROOT)}"
            )
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    http, realtime = load_contracts()
    write_or_check(HTTP_CONTRACT, serialize(http), args.check)
    write_or_check(REALTIME_CONTRACT, serialize(realtime), args.check)
    print(
        json.dumps(
            {
                "http_paths": len(http["paths"]),
                "schemas": len(http.get("components", {}).get("schemas", {})),
                "websockets": len(realtime["websockets"]),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
