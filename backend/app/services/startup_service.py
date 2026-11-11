"""Startup jobs: optional demo seed, optional PayPal sync, then refresh (FR-021, FR-040).

They run in one daemon thread, so the app answers /health at once (Render health checks and
free-tier wake-ups). No job ever stops the app: failures are logged and visible in the data.
"""

import logging
import threading
from dataclasses import dataclass

from sqlalchemy import Engine

from app.fx import FxGateway
from app.paypal import PayPalGateway, SessionFactory
from app.services.refresh_service import safe_refresh
from app.services.seed_service import count_seed_rows, seed_demo
from app.services.sync_service import run_startup_sync

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StartupJobs:
    seed_demo: bool  # SEED_DEMO_ON_STARTUP
    sync: bool  # STARTUP_SYNC_ENABLED

    @property
    def any(self) -> bool:
        return self.seed_demo or self.sync


@dataclass(frozen=True)
class StartupDeps:
    factory: SessionFactory
    engine: Engine
    gateway: PayPalGateway
    fx: FxGateway


def safe_seed(factory: SessionFactory) -> None:
    """Idempotent demo seed (rows labelled demo_seed); a failure is logged, never raised."""
    try:
        with factory() as session:
            added = seed_demo(session)
            session.commit()
            total = count_seed_rows(session)
            logger.info("Demo seed at startup: %d new, %d in total", added, total)
    except Exception:
        logger.exception("Demo seed at startup failed")


def run_startup_jobs(deps: StartupDeps, jobs: StartupJobs) -> None:
    if jobs.seed_demo:
        safe_seed(deps.factory)
    if jobs.sync:
        run_startup_sync(deps.factory, deps.engine, deps.gateway, deps.fx)  # refreshes after
    else:
        safe_refresh(deps.factory, deps.fx)  # leakage and FIRA status for the seeded rows


def start_startup_thread(deps: StartupDeps, jobs: StartupJobs) -> None:
    threading.Thread(
        target=run_startup_jobs, args=(deps, jobs), name="startup-jobs", daemon=True
    ).start()
