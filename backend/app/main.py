"""Create the FastAPI app: CORS, error handlers, routers, startup. Nothing else."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ROUTERS
from app.common.constants import LOCAL_FRONTEND_ORIGIN
from app.common.errors import register_error_handlers
from app.config import get_settings
from app.db import get_engine
from app.models import Base


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(get_engine())
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
    )
    register_error_handlers(app)
    for router in ROUTERS:
        app.include_router(router)
    return app


app = create_app()
