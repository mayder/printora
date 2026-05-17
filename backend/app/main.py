from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.checklists import build_post_update_checklist
from app.config import Settings, get_settings
from app.database import initialize_database
from app.moonraker import MoonrakerClient


def get_moonraker_client(settings: Settings) -> MoonrakerClient:
    return MoonrakerClient(
        base_url=settings.moonraker_url,
        timeout_seconds=settings.request_timeout_seconds,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    initialize_database(settings.database_path)
    yield


app = FastAPI(title="MayderPrintLab", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": "MayderPrintLab"}


@app.get("/api/moonraker/status")
async def moonraker_status() -> dict[str, Any]:
    settings = get_settings()
    client = get_moonraker_client(settings)
    try:
        printer_info, server_info, system_info, proc_stats = await _collect_status(client)
    except httpx.HTTPError as exc:
        return {
            "connected": False,
            "moonraker_url": settings.moonraker_url,
            "error": str(exc),
        }

    return {
        "connected": True,
        "moonraker_url": settings.moonraker_url,
        "printer": printer_info,
        "server": server_info,
        "system": system_info,
        "proc_stats": proc_stats,
    }


@app.get("/api/checklist/post-update")
async def post_update_checklist() -> dict[str, Any]:
    settings = get_settings()
    client = get_moonraker_client(settings)
    printer_info = await client.printer_info()
    server_info = await client.server_info()
    update_status = await client.update_status()
    return build_post_update_checklist(printer_info, server_info, update_status)


async def _collect_status(client: MoonrakerClient) -> tuple[dict[str, Any], ...]:
    printer_info = await client.printer_info()
    server_info = await client.server_info()
    system_info = await client.system_info()
    proc_stats = await client.proc_stats()
    return printer_info, server_info, system_info, proc_stats
