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
    request = make_request("203.0.113.5, 10.0.0.2")
    assert client_ip(request, trust_proxy_headers=True) == "203.0.113.5"
    assert client_ip(request, trust_proxy_headers=False) == "10.0.0.1"
