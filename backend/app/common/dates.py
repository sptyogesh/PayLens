"""UTC date helpers and the PayPal date-window splitter (research R4)."""

from datetime import UTC, datetime, timedelta


def utc_now() -> datetime:
    return datetime.now(UTC)


def ensure_utc(value: datetime) -> datetime:
    """Return an aware UTC datetime. Naive values are rejected to avoid silent shifts."""
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return value.astimezone(UTC)


def split_windows(start: datetime, end: datetime, max_days: int) -> list[tuple[datetime, datetime]]:
    """Split [start, end) into back-to-back windows of at most max_days.

    Each window's end is the next window's start, so there is no gap and no overlap.
    """
    start, end = ensure_utc(start), ensure_utc(end)
    if start >= end:
        raise ValueError("start must be before end")
    step = timedelta(days=max_days)
    windows: list[tuple[datetime, datetime]] = []
    cursor = start
    while cursor < end:
        window_end = min(cursor + step, end)
        windows.append((cursor, window_end))
        cursor = window_end
    return windows
