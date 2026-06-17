from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.auth import AuthRepository, set_current_auth_context
from app.database import connect_database, initialize_database
from app.social_catalog import SocialCatalogRepository
from app.routes import (
    audit,
    agents,
    auth,
    backups,
    calibration,
    can_monitor,
    checklists,
    firmware,
    frontend,
    maintenance,
    operation,
    plugins,
    print_profiles,
    printer_updates,
    printers,
    reports,
    search_discovery,
    setup,
    slicing,
    snapshots,
    social_catalog,
    social_moderation,
    social_notifications,
    social_ranking,
    social_safety,
    social_storage,
    system,
    technical_profiles,
    z_offset,
)
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    initialize_database(settings.database_path)
    with connect_database(settings.database_path) as connection:
        repository = SocialCatalogRepository(settings.database_path)
        repository.sync_all_communities(connection)
        repository.sync_default_feed_items(connection)
    yield


app = FastAPI(title="Printora", version="0.1.37", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def auth_context_middleware(request, call_next):
    set_current_auth_context(None)
    authorization = request.headers.get("authorization")
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            user = AuthRepository(get_settings().database_path).get_user_by_session(token.strip())
            set_current_auth_context(user)
    return await call_next(request)

_frontend_dist_dir = get_settings().frontend_dist_dir
_frontend_assets_dir = _frontend_dist_dir / "assets"
_frontend_brand_dir = _frontend_dist_dir / "brand"
if _frontend_assets_dir.is_dir():
    app.mount("/assets", StaticFiles(directory=_frontend_assets_dir), name="frontend-assets")
if _frontend_brand_dir.is_dir():
    app.mount("/brand", StaticFiles(directory=_frontend_brand_dir), name="frontend-brand")

app.include_router(audit.router)
app.include_router(agents.router)
app.include_router(auth.router)
app.include_router(backups.router)
app.include_router(calibration.router)
app.include_router(can_monitor.router)
app.include_router(checklists.router)
app.include_router(firmware.router)
app.include_router(maintenance.router)
app.include_router(operation.router)
app.include_router(plugins.router)
app.include_router(print_profiles.router)
app.include_router(printer_updates.router)
app.include_router(printers.router)
app.include_router(reports.router)
app.include_router(search_discovery.router)
app.include_router(setup.router)
app.include_router(slicing.router)
app.include_router(snapshots.router)
app.include_router(social_catalog.router)
app.include_router(social_moderation.router)
app.include_router(social_notifications.router)
app.include_router(social_ranking.router)
app.include_router(social_safety.router)
app.include_router(social_storage.router)
app.include_router(system.router)
app.include_router(technical_profiles.router)
app.include_router(z_offset.router)
app.include_router(frontend.router)
