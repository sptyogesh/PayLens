import itertools
from datetime import UTC, datetime, timedelta, timezone

import pytest
from freezegun import freeze_time

from app.common.constants import PAYPAL_WINDOW_DAYS
from app.common.dates import ensure_utc, split_windows, utc_now

START = datetime(2026, 8, 1, tzinfo=UTC)


def test_p1_75_day_range_splits_into_three_windows() -> None:
    windows = split_windows(START, START + timedelta(days=75), PAYPAL_WINDOW_DAYS)
    assert len(windows) == 3
    assert all(end - start <= timedelta(days=31) for start, end in windows)


def test_exactly_31_days_is_one_window() -> None:
    assert split_windows(START, START + timedelta(days=31), 31) == [
        (START, START + timedelta(days=31))
    ]


def test_windows_are_contiguous_without_gap_or_overlap() -> None:
    end = START + timedelta(days=90, hours=5)
    windows = split_windows(START, end, 31)
    assert windows[0][0] == START
    assert windows[-1][1] == end
    for (_, previous_end), (next_start, _) in itertools.pairwise(windows):
        assert previous_end == next_start


def test_start_must_be_before_end() -> None:
    with pytest.raises(ValueError, match="before"):
        split_windows(START, START, 31)


def test_naive_datetimes_are_rejected_and_offsets_converted() -> None:
    with pytest.raises(ValueError, match="aware"):
        ensure_utc(datetime(2026, 1, 1))  # noqa: DTZ001 - testing the naive case
    ist = timezone(timedelta(hours=5, minutes=30))
    assert ensure_utc(datetime(2026, 1, 1, 5, 30, tzinfo=ist)) == datetime(2026, 1, 1, tzinfo=UTC)


@freeze_time("2026-11-10 12:00:00")
def test_utc_now_is_aware_utc() -> None:
    assert utc_now() == datetime(2026, 11, 10, 12, tzinfo=UTC)
