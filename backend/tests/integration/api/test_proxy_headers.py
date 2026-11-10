"""Rate limits behind Render's proxy (hardening fix 1): only FORWARDED_ALLOW_IPS may set the client.

TestClient connects as host "testclient", so trusting "testclient" stands in for Render's proxy.
"""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.common.constants import RATE_LIMIT_SYNC
from app.config import get_settings

LIMIT, _ = RATE_LIMIT_SYNC


def sync_as(api: TestClient, forwarded_for: str) -> int:
    response = api.post("/sync", headers={"x-forwarded-for": forwarded_for})
    return int(response.status_code)


@pytest.fixture
def trusted_proxy(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("FORWARDED_ALLOW_IPS", "testclient")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.usefixtures("trusted_proxy")
def test_each_real_client_behind_the_proxy_has_its_own_limit(api: TestClient) -> None:
    assert [sync_as(api, "198.51.100.1") for _ in range(LIMIT)] == [200] * LIMIT
    assert sync_as(api, "198.51.100.1") == 429
    assert sync_as(api, "198.51.100.2") == 200  # another client is not blocked


@pytest.mark.usefixtures("trusted_proxy")
def test_spoofed_entries_sent_by_a_client_are_ignored(api: TestClient) -> None:
    # The proxy appends the real address last; whatever the client sent before it does not count.
    statuses = [sync_as(api, f"10.9.9.{n}, 198.51.100.7") for n in range(LIMIT + 1)]
    assert statuses == [200] * LIMIT + [429]


def test_headers_from_an_untrusted_peer_are_ignored(api: TestClient) -> None:
    # Default FORWARDED_ALLOW_IPS is 127.0.0.1, so "testclient" may not set the client address.
    statuses = [sync_as(api, f"198.51.100.{n}") for n in range(LIMIT + 1)]
    assert statuses == [200] * LIMIT + [429]
