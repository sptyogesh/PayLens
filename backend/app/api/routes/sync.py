"""POST /sync (rate limited, one at a time) and GET /sync/last (FR-019 to FR-021)."""

from typing import Annotated

from fastapi import APIRouter, Body, Depends
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_gateway, rate_limit
from app.common.constants import RATE_LIMIT_SYNC
from app.common.dates import utc_now
from app.common.types import SyncTrigger
from app.db import get_engine, get_session, get_session_factory
from app.paypal.gateway import PayPalGateway
from app.schemas.sync import SyncRequest, SyncRunOut
from app.services.sync_service import get_last_run, start_sync

router = APIRouter(tags=["sync"])


@router.post("/sync", dependencies=[Depends(rate_limit("sync", RATE_LIMIT_SYNC))])
def post_sync(
    factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
    engine: Annotated[Engine, Depends(get_engine)],
    gateway: Annotated[PayPalGateway, Depends(get_gateway)],
    body: Annotated[SyncRequest | None, Body()] = None,
) -> SyncRunOut:
    period = (body.start, body.end) if body else (None, None)
    run = start_sync(factory, engine, gateway, SyncTrigger.MANUAL, period)
    return SyncRunOut.from_model(run, utc_now())


@router.get("/sync/last")
def last_sync(session: Annotated[Session, Depends(get_session)]) -> SyncRunOut | None:
    run = get_last_run(session)
    return SyncRunOut.from_model(run, utc_now()) if run else None
