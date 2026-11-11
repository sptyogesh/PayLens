from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx

from app.common.errors import PayPalError
from app.common.http_client import make_client
from app.fakes.paypal_fake import FakePayPalGateway
from app.paypal import HttpPayPalGateway, TokenCache
from tests.fixtures.paypal.search import page, row

BASE = "https://api-m.sandbox.paypal.com"
START = datetime(2026, 10, 1, tzinfo=UTC)
END = datetime(2026, 10, 31, tzinfo=UTC)


def gateway() -> HttpPayPalGateway:
    respx.post(f"{BASE}/v1/oauth2/token").mock(
        return_value=httpx.Response(200, json={"access_token": "t", "expires_in": 3600})
    )
    client = make_client(BASE)
    return HttpPayPalGateway(client, TokenCache(client, "id", "secret"))


@respx.mock
def test_search_sends_exact_query_and_parses_rows() -> None:
    route = respx.get(f"{BASE}/v1/reporting/transactions").mock(
        return_value=httpx.Response(200, json=page([row("A"), row("B")], 1, 3))
    )
    result = gateway().search_transactions(START, END, 1)
    query = parse_qs(urlparse(str(route.calls[0].request.url)).query)
    assert {k: v[0] for k, v in query.items()} == {
        "start_date": "2026-10-01T00:00:00Z",
        "end_date": "2026-10-31T00:00:00Z",
        "fields": "all",
        "balance_affecting_records_only": "N",
        "page_size": "500",
        "page": "1",
    }
    assert [r.detail.transaction_info.transaction_id for r in result.rows] == ["A", "B"]
    assert result.rows[0].raw["transaction_info"]["transaction_id"] == "A"
    assert (result.page, result.total_pages) == (1, 3)


@respx.mock
def test_search_rejected_by_paypal_raises_safe_error() -> None:
    respx.get(f"{BASE}/v1/reporting/transactions").mock(return_value=httpx.Response(403))
    with pytest.raises(PayPalError) as error:
        gateway().search_transactions(START, END, 1)
    assert error.value.code == "PAYPAL_REJECTED"


def test_fake_returns_twelve_events_over_two_pages() -> None:
    now = datetime(2026, 11, 10, tzinfo=UTC)
    fake = FakePayPalGateway(now)
    first = fake.search_transactions(now - timedelta(days=31), now, 1)
    second = fake.search_transactions(now - timedelta(days=31), now, 2)
    assert (first.total_pages, len(first.rows), len(second.rows)) == (2, 6, 6)
    assert fake.search_transactions(now - timedelta(days=31), now, 3).rows == []
