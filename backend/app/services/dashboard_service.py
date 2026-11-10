"""Dashboard numbers for a period (FR-030 to FR-036). Totals come from the leakage engine."""

from datetime import datetime

from sqlalchemy.orm import Session

from app.common.constants import PERCENT_FACTOR, SIMULATED_FX_SPREAD
from app.common.money import to_percent_string
from app.common.periods import PERIOD_LABELS, DashboardPeriod, resolve
from app.engine.leakage import by_client, by_month, totals
from app.schemas.dashboard import BreakdownRowOut, DashboardOut, DashboardPeriodOut, TotalsOut
from app.services.leakage_query import Collected, collect


def get_dashboard(session: Session, period: DashboardPeriod, now: datetime) -> DashboardOut:
    start, _ = resolve(period, now)
    # The period ends "now"; no upper bound in the query so a payment recorded at this very
    # instant is still counted.
    return dashboard_from(collect(session, start, None), period, now)


def dashboard_from(data: Collected, period: DashboardPeriod, now: datetime) -> DashboardOut:
    """The dashboard for rows already collected for `period` (shared with the CA report)."""
    start, end = resolve(period, now)
    rows = data.rows
    return DashboardOut(
        period=DashboardPeriodOut(key=period, label=PERIOD_LABELS[period], start=start, end=end),
        totals=TotalsOut.of(totals(rows)) if rows else None,
        excluded_count=data.excluded_count,
        not_calculated_count=data.not_calculated_count,
        sources=data.sources,
        simulated_spread_percent=to_percent_string(SIMULATED_FX_SPREAD * PERCENT_FACTOR),
        by_month=[BreakdownRowOut.of(g) for g in by_month(rows)],
        by_client=[BreakdownRowOut.of(g) for g in by_client(rows)],
    )
