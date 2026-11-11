"""Frankfurter client against respx-mocked responses (never the real service)."""

from datetime import date
from decimal import Decimal

import httpx
import pytest
import respx

from app.common.errors import FxUnavailableError
from app.fx import FrankfurterGateway

BASE = "https://fx.test"
SATURDAY = date(2026, 11, 7)
URL = f"{BASE}/v2/rate/USD/INR"


@pytest.fixture
def gateway() -> FrankfurterGateway:
    return FrankfurterGateway(httpx.Client(base_url=BASE))


@respx.mock
def test_weekend_returns_friday_rate_exactly(gateway: FrankfurterGateway) -> None:
    route = respx.get(URL).respond(
        200, text='{"date":"2026-11-06","base":"USD","quote":"INR","rate":93.9212345678}'
    )
    quote = gateway.mid_rate("USD", SATURDAY)
    assert quote is not None
    assert quote.rate == Decimal("93.921235")
    assert quote.published_date == date(2026, 11, 6)
    assert quote.source == "frankfurter_ecb"
    assert route.calls.last.request.url.params["date"] == "2026-11-07"
    assert route.calls.last.request.url.params["providers"] == "ecb"


@respx.mock
@pytest.mark.parametrize("status", [400, 404, 422])
def test_unknown_currency_means_no_rate(gateway: FrankfurterGateway, status: int) -> None:
    respx.get(URL).respond(status, json={"message": "invalid currency"})
    assert gateway.mid_rate("USD", SATURDAY) is None


@respx.mock
@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(503),
        httpx.Response(200, text="not json"),
        httpx.Response(200, json={"date": "2026-11-06", "base": "USD", "quote": "INR"}),
        httpx.Response(200, json={"date": "2026-11-06", "base": "GBP", "quote": "INR", "rate": 1}),
        httpx.Response(200, json={"date": "2026-11-08", "base": "USD", "quote": "INR", "rate": 1}),
        httpx.Response(200, json={"date": "2026-11-06", "base": "USD", "quote": "INR", "rate": 0}),
    ],
)
def test_bad_answers_are_unavailable(gateway: FrankfurterGateway, response: httpx.Response) -> None:
    respx.get(URL).mock(return_value=response)
    with pytest.raises(FxUnavailableError):
        gateway.mid_rate("USD", SATURDAY)


@respx.mock
def test_network_error_is_unavailable(gateway: FrankfurterGateway) -> None:
    respx.get(URL).mock(side_effect=httpx.ConnectTimeout("slow"))
    with pytest.raises(FxUnavailableError):
        gateway.mid_rate("USD", SATURDAY)
