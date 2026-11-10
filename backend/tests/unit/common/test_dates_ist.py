from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from app.common.dates import ist_date, ist_month_start


def test_ist_date_moves_late_utc_evening_to_next_day() -> None:
    assert ist_date(datetime(2026, 11, 6, 19, 0, tzinfo=UTC)) == date(2026, 11, 7)
    assert ist_date(datetime(2026, 11, 6, 18, 29, tzinfo=UTC)) == date(2026, 11, 6)


def test_ist_date_rejects_naive_datetimes() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        ist_date(datetime(2026, 11, 6, 12, 0))  # noqa: DTZ001 - naive on purpose


def test_month_start_is_midnight_ist_in_utc() -> None:
    now = datetime(2026, 11, 10, 9, 0, tzinfo=UTC)
    assert ist_month_start(now, 0) == datetime(2026, 10, 31, 18, 30, tzinfo=UTC)
    assert ist_month_start(now, 2) == datetime(2026, 8, 31, 18, 30, tzinfo=UTC)


def test_month_start_crosses_the_year_and_uses_ist_month() -> None:
    # 31 Jan 19:00 UTC is already 1 Feb in India.
    now = datetime(2027, 1, 31, 19, 0, tzinfo=UTC)
    assert ist_month_start(now, 0) == datetime(2027, 1, 31, 18, 30, tzinfo=UTC)
    assert ist_month_start(now, 2) == datetime(2026, 11, 30, 18, 30, tzinfo=UTC)
    ist = timezone(timedelta(hours=5, minutes=30))
    assert ist_month_start(now, 0).astimezone(ist).day == 1
