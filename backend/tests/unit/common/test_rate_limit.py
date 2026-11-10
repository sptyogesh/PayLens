from unittest.mock import Mock

import pytest

from app.common.errors import RateLimitedError
from app.common.rate_limit import FixedWindowLimiter, check_rate_limit, client_ip


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_allows_limit_then_rejects_with_retry_after() -> None:
    clock = FakeClock()
    limiter = FixedWindowLimiter(3, 60, clock)
    assert [limiter.hit("ip") for _ in range(3)] == [None, None, None]
    clock.now += 10
    assert limiter.hit("ip") == 50


def test_window_resets_and_ips_are_independent() -> None:
    clock = FakeClock()
    limiter = FixedWindowLimiter(1, 60, clock)
    assert limiter.hit("a") is None
    assert limiter.hit("b") is None
    assert limiter.hit("a") is not None
    clock.now += 60
    assert limiter.hit("a") is None


def test_check_rate_limit_raises_429_error() -> None:
    limiter = FixedWindowLimiter(0, 60, FakeClock())
    with pytest.raises(RateLimitedError) as error:
        check_rate_limit(limiter, "ip")
    assert error.value.http_status == 429
    assert error.value.retry_after_s == 60


def make_request(forwarded: str | None, host: str = "10.0.0.1") -> Mock:
    request = Mock()
    request.headers = {"x-forwarded-for": forwarded} if forwarded else {}
    request.client.host = host
    return request


def test_proxy_header_used_only_when_trusted() -> None:
    # The client may send any first entry; the trusted proxy appends the real address last.
    request = make_request("1.2.3.4, 203.0.113.5")
    assert client_ip(request, trust_proxy_headers=True) == "203.0.113.5"
    assert client_ip(request, trust_proxy_headers=False) == "10.0.0.1"


def test_spoofed_first_entries_share_the_real_clients_bucket() -> None:
    limiter = FixedWindowLimiter(1, 60, clock=lambda: 0.0)
    keys = {client_ip(make_request(f"{n}.0.0.1, 203.0.113.5"), True) for n in range(5)}
    assert keys == {"203.0.113.5"}
    assert limiter.hit("203.0.113.5") is None and limiter.hit("203.0.113.5") is not None


def test_finished_windows_are_pruned() -> None:
    now = [0.0]
    limiter = FixedWindowLimiter(1, 60, clock=lambda: now[0])
    for n in range(1002):
        limiter.hit(f"ip-{n}")
    now[0] = 61.0
    limiter.hit("late")
    assert len(limiter._windows) == 1
