import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.common.dates import utc_now
from app.common.errors import InvalidPeriodError, PayPalError, SyncInProgressError
from app.common.types import SyncOutcome, SyncTrigger
from app.fakes.paypal_fake import FakePayPalGateway
from app.models import SyncRun
from app.paypal.dto import SearchPage
from app.schemas.sync import SyncRunOut
from app.services.sync_lock import sync_lock
from app.services.sync_service import get_last_run, run_startup_sync, start_sync


class FailingGateway(FakePayPalGateway):
    def search_transactions(self, start: datetime, end: datetime, page: int) -> SearchPage:
        raise PayPalError("PayPal is not responding right now.")


def test_success_records_counts(session_factory: sessionmaker[Session], db_engine: Engine) -> None:
    run = start_sync(session_factory, db_engine, FakePayPalGateway(), SyncTrigger.MANUAL)
    assert run.outcome is SyncOutcome.SUCCESS
    assert (run.added, run.updated, run.skipped, run.windows_total) == (10, 0, 2, 3)
    again = start_sync(session_factory, db_engine, FakePayPalGateway(), SyncTrigger.MANUAL)
    assert (again.added, again.updated, again.skipped) == (0, 10, 2)


def test_paypal_failure_is_recorded_with_safe_message(
    session_factory: sessionmaker[Session], db_engine: Engine
) -> None:
    run = start_sync(session_factory, db_engine, FailingGateway(), SyncTrigger.MANUAL)
    assert (run.outcome, run.error_code) == (SyncOutcome.FAILED, "PAYPAL_UNAVAILABLE")
    assert run.error_message == "PayPal is not responding right now."


@pytest.mark.parametrize(
    "period",
    [
        (datetime(2026, 11, 2, tzinfo=UTC), datetime(2026, 11, 1, tzinfo=UTC)),
        (None, utc_now() + timedelta(days=1)),
    ],
)
def test_invalid_period_is_rejected(
    session_factory: sessionmaker[Session], db_engine: Engine, period: tuple[datetime | None, ...]
) -> None:
    with pytest.raises(InvalidPeriodError):
        start_sync(session_factory, db_engine, FakePayPalGateway(), SyncTrigger.MANUAL, period)  # type: ignore[arg-type]


def test_second_sync_is_refused_while_one_runs(
    session_factory: sessionmaker[Session], db_engine: Engine
) -> None:
    with sync_lock(db_engine), pytest.raises(SyncInProgressError):
        start_sync(session_factory, db_engine, FakePayPalGateway(), SyncTrigger.MANUAL)


def test_startup_failure_is_recorded_and_not_raised(
    session_factory: sessionmaker[Session], db_engine: Engine, db_session: Session
) -> None:
    run_startup_sync(session_factory, db_engine, FailingGateway())
    last = get_last_run(db_session)
    assert last is not None
    assert (last.trigger, last.outcome) == (SyncTrigger.STARTUP, SyncOutcome.FAILED)


def test_stale_running_row_is_reported_as_failed() -> None:
    started = datetime(2026, 11, 10, 9, tzinfo=UTC)
    run = SyncRun(
        id=uuid.uuid4(),
        trigger=SyncTrigger.MANUAL,
        period_start=started - timedelta(days=90),
        period_end=started,
        started_at=started,
        outcome=SyncOutcome.RUNNING,
        windows_total=3,
        windows_done=1,
        added=0,
        updated=0,
        skipped=0,
        flagged=0,
    )
    out = SyncRunOut.from_model(run, started + timedelta(minutes=11))
    assert out.outcome is SyncOutcome.FAILED
    assert out.error is not None and out.error.code == "SYNC_INTERRUPTED"
    assert SyncRunOut.from_model(run, started + timedelta(minutes=5)).outcome is SyncOutcome.RUNNING
