"""Dashboard periods in India time (FR-031, data-model.md). Reused by chat and report.

Keys and labels must match frontend/lib/constants.ts PERIOD_OPTIONS.
"""

from datetime import datetime
from enum import StrEnum
from typing import Final

from app.common.dates import ensure_utc, ist_month_start


class DashboardPeriod(StrEnum):
    THIS_MONTH = "this_month"
    LAST_3_MONTHS = "last_3_months"
    ALL_TIME = "all_time"


DEFAULT_PERIOD: Final = DashboardPeriod.LAST_3_MONTHS
PERIOD_LABELS: Final = {
    DashboardPeriod.THIS_MONTH: "This month",
    DashboardPeriod.LAST_3_MONTHS: "Last 3 months",
    DashboardPeriod.ALL_TIME: "All time",
}
MONTHS_BACK: Final = {DashboardPeriod.THIS_MONTH: 0, DashboardPeriod.LAST_3_MONTHS: 2}

Bounds = tuple[datetime | None, datetime | None]


def resolve(period: DashboardPeriod, now: datetime) -> Bounds:
    """[start, end] in UTC; both None for all time. Months start at midnight IST."""
    if period is DashboardPeriod.ALL_TIME:
        return None, None
    return ist_month_start(now, MONTHS_BACK[period]), ensure_utc(now)
