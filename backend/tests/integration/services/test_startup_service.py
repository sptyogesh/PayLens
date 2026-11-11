"""Startup jobs (FR-021, FR-040): idempotent demo seed, sync, refresh; failures never raise."""

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.fakes.fx_fake import FakeFxGateway
from app.fakes.paypal_fake import FakePayPalGateway
from app.models import Transaction
from app.services.seed_service import count_seed_rows
from app.services.startup_service import StartupDeps, StartupJobs, run_startup_jobs
from app.services.sync_service import get_last_run

Factory = sessionmaker[Session]


def deps(factory: Factory, engine: Engine) -> StartupDeps:
    return StartupDeps(factory, engine, FakePayPalGateway(), FakeFxGateway())


def test_seed_job_is_idempotent_across_restarts_and_calculates_leakage(
    session_factory: Factory, db_engine: Engine
) -> None:
    jobs = StartupJobs(seed_demo=True, sync=False)
    run_startup_jobs(deps(session_factory, db_engine), jobs)
    run_startup_jobs(deps(session_factory, db_engine), jobs)  # a free-tier wake-up restarts
    with session_factory() as session:
        assert count_seed_rows(session) == 24
        assert get_last_run(session) is None  # sync was off
        rows = list(session.scalars(select(Transaction)))
    assert len(rows) == 24 and all(row.total_leakage_inr is not None for row in rows)


def test_seed_and_sync_both_run(session_factory: Factory, db_engine: Engine) -> None:
    run_startup_jobs(deps(session_factory, db_engine), StartupJobs(seed_demo=True, sync=True))
    with session_factory() as session:
        assert count_seed_rows(session) == 24
        assert get_last_run(session) is not None


def test_seed_off_adds_nothing(session_factory: Factory, db_engine: Engine) -> None:
    run_startup_jobs(deps(session_factory, db_engine), StartupJobs(seed_demo=False, sync=False))
    with session_factory() as session:
        assert count_seed_rows(session) == 0


def test_seed_failure_is_logged_and_the_other_jobs_still_run(
    session_factory: Factory,
    db_engine: Engine,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    def broken(_session: Session) -> int:
        raise RuntimeError("database went away")

    monkeypatch.setattr("app.services.startup_service.seed_demo", broken)
    run_startup_jobs(deps(session_factory, db_engine), StartupJobs(seed_demo=True, sync=True))
    assert "Demo seed at startup failed" in caplog.text
    with session_factory() as session:
        assert count_seed_rows(session) == 0
        assert get_last_run(session) is not None
