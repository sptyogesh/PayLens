"""Create the FastAPI app: CORS, error handlers, routers, startup. Nothing else."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

from app.api.deps import get_fx_gateway, get_gateway
from app.api.routes import ROUTERS
from app.common.constants import LOCAL_FRONTEND_ORIGIN
from app.common.errors import register_error_handlers
from app.config import get_settings
from app.db import get_engine, get_session_factory
from app.models import Base
from app.services.sync_service import start_startup_sync_thread


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(get_engine())
    if get_settings().startup_sync_enabled:
        start_startup_sync_thread(
            get_session_factory(), get_engine(), get_gateway(), get_fx_gateway()
        )
    yield


def allowed_origins() -> list[str]:
    frontend_url = get_settings().frontend_url.rstrip("/")
    return [origin for origin in (frontend_url, LOCAL_FRONTEND_ORIGIN) if origin]


def create_app() -> FastAPI:
    app = FastAPI(title="PayLens API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins(),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        expose_headers=["Content-Disposition"],  # CA report file name (005)
    )
    # Added last, so it runs first: the client address is fixed before CORS and rate limits.
    # Only FORWARDED_ALLOW_IPS proxies may set it; uvicorn's own handling is turned off in the
    # start command (--no-proxy-headers) so this setting is the single source.
    app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=get_settings().forwarded_allow_ips)
    register_error_handlers(app)
    for router in ROUTERS:
        app.include_router(router)
    return app


app = create_app()
