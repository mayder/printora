from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.database import initialize_database
from app.routes import (
    audit,
    backups,
    calibration,
    can_monitor,
    checklists,
    firmware,
    frontend,
    maintenance,
    operation,
    plugins,
    printer_updates,
    printers,
    reports,
    snapshots,
    system,
    z_offset,
)
from app.routes.support import _read_printer_print_hours, _send_and_monitor_gcode


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    initialize_database(settings.database_path)
    yield


app = FastAPI(title="Printora", version="0.1.12", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["*"],
)

_frontend_dist_dir = get_settings().frontend_dist_dir
_frontend_assets_dir = _frontend_dist_dir / "assets"
_frontend_brand_dir = _frontend_dist_dir / "brand"
if _frontend_assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_frontend_assets_dir), name="frontend-assets")
if _frontend_brand_dir.is_dir():
    app.mount("/brand", StaticFiles(directory=_frontend_brand_dir), name="frontend-brand")

app.include_router(audit.router)
app.include_router(backups.router)
app.include_router(calibration.router)
app.include_router(can_monitor.router)
app.include_router(checklists.router)
app.include_router(firmware.router)
app.include_router(maintenance.router)
app.include_router(operation.router)
app.include_router(plugins.router)
app.include_router(printer_updates.router)
app.include_router(printers.router)
app.include_router(reports.router)
app.include_router(snapshots.router)
app.include_router(system.router)
app.include_router(z_offset.router)
app.include_router(frontend.router)
