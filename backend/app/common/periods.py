"""Periods in India time (FR-031, 003 data-model.md). Reused by dashboard, chat and report.

Dashboard keys and labels must match frontend/lib/constants.ts PERIOD_OPTIONS. Named chat periods
use calendar quarters and the Indian financial year (1 Apr - 31 Mar), resolved as half-open UTC
ranges [start, end) whose days begin at midnight IST.
"""

from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from typing import Final

from pydantic import BaseModel, ConfigDict

from app.common.constants import (
    FINANCIAL_YEAR_START_MONTH,
    LAST_3_MONTHS_BACK,
    MONTH_LABEL_FORMAT,
    MONTHS_IN_YEAR,
    NAMED_PERIOD_LABELS,
    PERIOD_NAMED_LABEL,
    PERIOD_RANGE_LABEL,
    QUARTER_MONTHS,
)
from app.common.dates import IST, ensure_utc, ist_date, ist_month_start


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


class NamedPeriod(StrEnum):
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    LAST_3_MONTHS = "last_3_months"
    THIS_QUARTER = "this_quarter"
    LAST_QUARTER = "last_quarter"
    THIS_FINANCIAL_YEAR = "this_financial_year"
    LAST_FINANCIAL_YEAR = "last_financial_year"
    ALL_TIME = "all_time"


DEFAULT_NAMED_PERIOD: Final = NamedPeriod.LAST_3_MONTHS


class ResolvedPeriod(BaseModel):
    """UTC bounds [start, end) for queries, inclusive IST dates and a label for people.

    `end` None means "up to now"; `start` None means "from the beginning" (all time).
    """

    model_config = ConfigDict(frozen=True)

    start: datetime | None
    end: datetime | None
    label: str
    start_date: date | None
    end_date: date | None


# A month index counts months since year 0 (year * 12 + month - 1), so subtraction just works.
MonthSpan = tuple[int, int | None]  # first month index, end month index (exclusive) or None


def _quarter_start(month: int) -> int:
    return month - (month % MONTHS_IN_YEAR) % QUARTER_MONTHS


def _financial_year_start(month: int) -> int:
    return month - (month % MONTHS_IN_YEAR - (FINANCIAL_YEAR_START_MONTH - 1)) % MONTHS_IN_YEAR


SPANS: Final[dict[NamedPeriod, Callable[[int], MonthSpan]]] = {
    NamedPeriod.THIS_MONTH: lambda m: (m, None),
    NamedPeriod.LAST_MONTH: lambda m: (m - 1, m),
    NamedPeriod.LAST_3_MONTHS: lambda m: (m - LAST_3_MONTHS_BACK, None),
    NamedPeriod.THIS_QUARTER: lambda m: (_quarter_start(m), None),
    NamedPeriod.LAST_QUARTER: lambda m: (_quarter_start(m) - QUARTER_MONTHS, _quarter_start(m)),
    NamedPeriod.THIS_FINANCIAL_YEAR: lambda m: (_financial_year_start(m), None),
    NamedPeriod.LAST_FINANCIAL_YEAR: lambda m: (
        _financial_year_start(m) - MONTHS_IN_YEAR,
        _financial_year_start(m),
    ),
}


def _month_first_day(index: int) -> date:
    return date(index // MONTHS_IN_YEAR, index % MONTHS_IN_YEAR + 1, 1)


def ist_day_start(day: date) -> datetime:
    """Midnight IST at the start of `day`, as UTC."""
    return datetime(day.year, day.month, day.day, tzinfo=IST).astimezone(UTC)


def format_day(day: date) -> str:
    """date(2026, 7, 1) -> "1 Jul 2026"."""
    return f"{day.day} {day.strftime(MONTH_LABEL_FORMAT)}"


def range_label(start: date, end: date) -> str:
    return PERIOD_RANGE_LABEL.format(start=format_day(start), end=format_day(end))


def resolve_named(period: NamedPeriod, now: datetime) -> ResolvedPeriod:
    """Resolve a named period in IST. Current periods end at `now` (label: today's IST date)."""
    name = NAMED_PERIOD_LABELS[period.value]
    if period is NamedPeriod.ALL_TIME:
        return ResolvedPeriod(start=None, end=None, label=name, start_date=None, end_date=None)
    today = ist_date(now)
    first, stop = SPANS[period](today.year * MONTHS_IN_YEAR + today.month - 1)
    start_date = _month_first_day(first)
    stop_date = _month_first_day(stop) if stop is not None else None
    end_date = stop_date - timedelta(days=1) if stop_date is not None else today
    return ResolvedPeriod(
        start=ist_day_start(start_date),
        end=ist_day_start(stop_date) if stop_date is not None else None,
        label=PERIOD_NAMED_LABEL.format(name=name, range=range_label(start_date, end_date)),
        start_date=start_date,
        end_date=end_date,
    )


def resolve_dates(start: date, end: date, now: datetime) -> ResolvedPeriod:
    """Inclusive IST dates -> [start midnight IST, day after end midnight IST).

    `now` is accepted so both resolvers share one call shape; explicit dates do not depend on it.
    """
    ensure_utc(now)
    if start > end:
        raise ValueError("start date must not be after end date")
    return ResolvedPeriod(
        start=ist_day_start(start),
        end=ist_day_start(end + timedelta(days=1)),
        label=range_label(start, end),
        start_date=start,
        end_date=end,
    )
