from datetime import UTC, datetime

from app.common.periods import DashboardPeriod, resolve

NOW = datetime(2026, 11, 10, 9, 0, tzinfo=UTC)


def test_this_month_starts_at_midnight_ist() -> None:
    assert resolve(DashboardPeriod.THIS_MONTH, NOW) == (
        datetime(2026, 10, 31, 18, 30, tzinfo=UTC),
        NOW,
    )


def test_last_3_months_includes_two_previous_months() -> None:
    start, end = resolve(DashboardPeriod.LAST_3_MONTHS, NOW)
    assert (start, end) == (datetime(2026, 8, 31, 18, 30, tzinfo=UTC), NOW)


def test_all_time_has_no_bounds() -> None:
    assert resolve(DashboardPeriod.ALL_TIME, NOW) == (None, None)
