"""003 T002: named chat periods in IST — calendar quarters and the Indian financial year."""

from datetime import UTC, date, datetime

import pytest
from freezegun import freeze_time

from app.common.dates import utc_now
from app.common.periods import (
    DashboardPeriod,
    NamedPeriod,
    resolve,
    resolve_dates,
    resolve_named,
)

NOW = datetime(2026, 11, 10, 6, 0, tzinfo=UTC)  # 11:30 IST, 10 Nov 2026
P = NamedPeriod


def utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=UTC)


def dates(period: NamedPeriod, now: datetime = NOW) -> tuple[date | None, date | None]:
    resolved = resolve_named(period, now)
    return resolved.start_date, resolved.end_date


def test_this_month_runs_from_midnight_ist_to_now() -> None:
    resolved = resolve_named(P.THIS_MONTH, NOW)
    assert (resolved.start, resolved.end) == (utc(2026, 10, 31, 18, 30), None)
    assert resolved.label == "This month (1 Nov 2026 – 10 Nov 2026)"


def test_last_month_is_a_closed_half_open_range() -> None:
    resolved = resolve_named(P.LAST_MONTH, NOW)
    assert (resolved.start, resolved.end) == (utc(2026, 9, 30, 18, 30), utc(2026, 10, 31, 18, 30))
    assert resolved.label == "Last month (1 Oct 2026 – 31 Oct 2026)"


def test_last_3_months_matches_the_dashboard() -> None:
    resolved = resolve_named(P.LAST_3_MONTHS, NOW)
    assert resolved.start == resolve(DashboardPeriod.LAST_3_MONTHS, NOW)[0]
    assert resolved.label == "Last 3 months (1 Sep 2026 – 10 Nov 2026)"


def test_quarters_are_calendar_quarters() -> None:
    assert dates(P.THIS_QUARTER) == (date(2026, 10, 1), date(2026, 11, 10))
    resolved = resolve_named(P.LAST_QUARTER, NOW)
    assert resolved.label == "Last quarter (1 Jul 2026 – 30 Sep 2026)"
    assert (resolved.start, resolved.end) == (utc(2026, 6, 30, 18, 30), utc(2026, 9, 30, 18, 30))


def test_financial_years_run_april_to_march() -> None:
    assert dates(P.THIS_FINANCIAL_YEAR) == (date(2026, 4, 1), date(2026, 11, 10))
    assert dates(P.LAST_FINANCIAL_YEAR) == (date(2025, 4, 1), date(2026, 3, 31))
    assert resolve_named(P.LAST_FINANCIAL_YEAR, NOW).end == utc(2026, 3, 31, 18, 30)


def test_all_time_has_no_bounds() -> None:
    resolved = resolve_named(P.ALL_TIME, NOW)
    assert (resolved.start, resolved.end, resolved.start_date, resolved.end_date) == (None,) * 4
    assert resolved.label == "All time"


def test_year_boundary() -> None:
    january = utc(2027, 1, 5, 6, 0)
    assert dates(P.LAST_MONTH, january) == (date(2026, 12, 1), date(2026, 12, 31))
    assert dates(P.LAST_QUARTER, january) == (date(2026, 10, 1), date(2026, 12, 31))
    assert dates(P.LAST_3_MONTHS, january) == (date(2026, 11, 1), date(2027, 1, 5))
    assert dates(P.THIS_FINANCIAL_YEAR, january) == (date(2026, 4, 1), date(2027, 1, 5))


def test_new_year_starts_at_midnight_ist() -> None:
    before, after = utc(2026, 12, 31, 18, 29), utc(2026, 12, 31, 18, 30)
    assert dates(P.THIS_MONTH, before)[0] == date(2026, 12, 1)
    assert dates(P.THIS_MONTH, after)[0] == date(2027, 1, 1)


def test_financial_year_boundary_at_midnight_ist() -> None:
    march_31_late, april_1 = utc(2027, 3, 31, 18, 29), utc(2027, 3, 31, 18, 30)
    assert dates(P.THIS_FINANCIAL_YEAR, march_31_late) == (date(2026, 4, 1), date(2027, 3, 31))
    assert dates(P.THIS_FINANCIAL_YEAR, april_1) == (date(2027, 4, 1), date(2027, 4, 1))
    assert dates(P.LAST_FINANCIAL_YEAR, april_1) == (date(2026, 4, 1), date(2027, 3, 31))


def test_quarter_boundary_at_midnight_ist() -> None:
    sep_30_late, oct_1 = utc(2026, 9, 30, 18, 29), utc(2026, 9, 30, 18, 30)
    assert dates(P.THIS_QUARTER, sep_30_late) == (date(2026, 7, 1), date(2026, 9, 30))
    assert dates(P.THIS_QUARTER, oct_1) == (date(2026, 10, 1), date(2026, 10, 1))
    assert dates(P.LAST_QUARTER, oct_1) == (date(2026, 7, 1), date(2026, 9, 30))


@pytest.mark.parametrize("period", [p for p in NamedPeriod if p is not NamedPeriod.ALL_TIME])
def test_every_period_is_well_formed(period: NamedPeriod) -> None:
    resolved = resolve_named(period, NOW)
    assert resolved.start_date is not None and resolved.end_date is not None
    assert resolved.start_date <= resolved.end_date <= date(2026, 11, 10)
    assert resolved.start is not None and resolved.start.tzinfo is not None
    assert resolved.end is None or resolved.start < resolved.end


@freeze_time("2026-11-10 06:00:00")
def test_resolves_from_the_frozen_clock() -> None:
    assert resolve_named(P.THIS_MONTH, utc_now()).end_date == date(2026, 11, 10)


def test_explicit_dates_are_inclusive_ist_days() -> None:
    resolved = resolve_dates(date(2026, 8, 1), date(2026, 9, 15), NOW)
    assert (resolved.start, resolved.end) == (utc(2026, 7, 31, 18, 30), utc(2026, 9, 15, 18, 30))
    assert resolved.label == "1 Aug 2026 – 15 Sep 2026"
    assert resolve_dates(date(2026, 8, 1), date(2026, 8, 1), NOW).end == utc(2026, 8, 1, 18, 30)


def test_explicit_dates_must_be_in_order() -> None:
    with pytest.raises(ValueError, match="after"):
        resolve_dates(date(2026, 9, 2), date(2026, 9, 1), NOW)


def test_naive_now_is_rejected() -> None:
    with pytest.raises(ValueError, match="aware"):
        resolve_named(P.THIS_MONTH, datetime(2026, 11, 10))  # noqa: DTZ001 - naive on purpose
