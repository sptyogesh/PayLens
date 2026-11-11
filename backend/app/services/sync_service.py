"""Run a sync and record it in sync_runs (FR-019 to FR-022)."""

import logging
import uuid
from datetime import datetime, timedelta

from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.common.constants import SYNC_DEFAULT_DAYS, SYNC_MAX_HISTORY_DAYS
from app.common.dates import ensure_utc, utc_now
from app.common.errors import AppError, InvalidPeriodError
from app.common.types import SyncOutcome, SyncTrigger
from app.fx import FxGateway
from app.models import SyncRun
from app.paypal import PayPalGateway, SessionFactory, SyncResult, run_sync
from app.services.refresh_service import safe_refresh
from app.services.sync_lock import sync_lock

logger = logging.getLogger(__name__)

INVALID_PERIOD_MESSAGE = (
    "The sync period must start before it ends, must not end in the future and must start"
    " within the last 3 years."
)
INTERNAL_SYNC_MESSAGE = "The sync stopped because of an unexpected error."


def resolve_period(
    start: datetime | None, end: datetime | None, now: datetime
) -> tuple[datetime, datetime]:
    period_end = ensure_utc(end) if end else now
    period_start = ensure_utc(start) if start else period_end - timedelta(days=SYNC_DEFAULT_DAYS)
    too_old = period_start < now - timedelta(days=SYNC_MAX_HISTORY_DAYS)
    if period_start >= period_end or period_end > now or too_old:
        raise InvalidPeriodError(INVALID_PERIOD_MESSAGE)
    return period_start, period_end


def outcome_of(result: SyncResult) -> SyncOutcome:
    if result.error is None:
        return SyncOutcome.PARTIAL if result.truncated else SyncOutcome.SUCCESS
    return SyncOutcome.PARTIAL if result.windows_done > 0 else SyncOutcome.FAILED


def create_run(
    factory: SessionFactory, trigger: SyncTrigger, period: tuple[datetime, datetime]
) -> uuid.UUID:
    with factory() as session:
        run = SyncRun(
            trigger=trigger,
            period_start=period[0],
            period_end=period[1],
            started_at=utc_now(),
            outcome=SyncOutcome.RUNNING,
        )
        session.add(run)
        session.commit()
        return run.id


def finish_run(factory: SessionFactory, run_id: uuid.UUID, result: SyncResult) -> SyncRun:
    with factory() as session:
        run = session.get_one(SyncRun, run_id)
        run.finished_at = utc_now()
        run.outcome = outcome_of(result)
        run.windows_total, run.windows_done = result.windows_total, result.windows_done
        run.added, run.updated = result.added, result.updated
        run.skipped, run.flagged = result.skipped, result.flagged
        if result.error is not None:
            run.error_code, run.error_message = result.error.code, result.error.message
        session.commit()
        return run


def start_sync(
    factory: SessionFactory,
    engine: Engine,
    gateway: PayPalGateway,
    trigger: SyncTrigger,
    period: tuple[datetime | None, datetime | None] = (None, None),
) -> SyncRun:
    start, end = resolve_period(*period, utc_now())
    with sync_lock(engine):
        run_id = create_run(factory, trigger, (start, end))
        result = SyncResult()
        try:
            run_sync(factory, gateway, start, end, result)
        except Exception:
            result.error = result.error or AppError(INTERNAL_SYNC_MESSAGE)
            finish_run(factory, run_id, result)  # keeps the windows that were stored
            raise
        return finish_run(factory, run_id, result)


def get_last_run(session: Session) -> SyncRun | None:
    return session.scalar(select(SyncRun).order_by(SyncRun.started_at.desc()).limit(1))


def run_startup_sync(
    factory: SessionFactory, engine: Engine, gateway: PayPalGateway, fx: FxGateway
) -> None:
    """Startup sync never stops the app; its result is visible through GET /sync/last (FR-021).
    Leakage is recalculated afterwards even if the sync failed (seeded rows still need it)."""
    try:
        start_sync(factory, engine, gateway, SyncTrigger.STARTUP)
    except AppError as error:
        logger.warning("Startup sync did not run: %s", error.code)
    except Exception:
        logger.exception("Startup sync failed unexpectedly")
    safe_refresh(factory, fx)
