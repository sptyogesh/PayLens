"""GET /dashboard?period=: leakage cards and breakdowns for a period (FR-030 to FR-036)."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.dates import utc_now
from app.common.periods import DEFAULT_PERIOD, DashboardPeriod
from app.db import get_session
from app.schemas.dashboard import DashboardOut
from app.services.dashboard_service import get_dashboard

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(
    session: Annotated[Session, Depends(get_session)],
    period: DashboardPeriod = DEFAULT_PERIOD,
) -> DashboardOut:
    return get_dashboard(session, period, utc_now())
