from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.agent_channel import agent_ws_manager
from app.auth import AuthRepository, set_current_auth_context
from app.database import connect_database, initialize_database
from app.idempotency_middleware import idempotency_middleware as apply_idempotency
from app.rate_limit_middleware import redis_rate_limit_middleware as apply_rate_limit
from app.modules import module_routers
from app.modules.platform.realtime_broker import RealtimeBroker
from app.modules.platform.recomposable_redis import RecomposableRedis
from app.operational import request_observability_middleware
from app.social_catalog import SocialCatalogRepository
@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    initialize_database(settings.database_path)
    with connect_database(settings.database_path) as connection:
        repository = SocialCatalogRepository(settings.database_path)
        repository.sync_all_communities(connection)
        repository.sync_default_feed_items(connection)
    redis_service = RecomposableRedis(settings.redis_url, settings.redis_prefix, settings.redis_timeout_seconds)
    agent_ws_manager.configure(settings.database_path, redis_service)
    realtime_broker = RealtimeBroker(redis_service, agent_ws_manager.handle_notification)
    await realtime_broker.start()
    app.state.recomposable_redis = redis_service
    app.state.realtime_broker = realtime_broker
    try:
        yield
    finally:
        await agent_ws_manager.disconnect_all()
        await realtime_broker.stop()


app = FastAPI(title="Printora", version="0.1.41", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
)


@app.middleware("http")
async def observability_middleware(request, call_next):
    return await request_observability_middleware(request, call_next)


@app.middleware("http")
async def durable_idempotency_middleware(request, call_next):
    return await apply_idempotency(request, call_next)


@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    return await apply_rate_limit(request, call_next)


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

for module_router in module_routers():
    app.include_router(module_router)
