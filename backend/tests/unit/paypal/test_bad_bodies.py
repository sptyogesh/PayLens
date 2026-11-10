"""Review fixes: non-JSON PayPal bodies and an already-captured order map to safe errors."""

from datetime import UTC, datetime

import httpx
import pytest
import respx

from app.common.errors import PaymentDeclinedError, PayPalError
from app.common.http_client import make_client
from app.paypal import HttpPayPalGateway, TokenCache
from app.paypal.orders_api import ALREADY_CAPTURED_MESSAGE, DECLINED_MESSAGE

BASE = "https://api-m.sandbox.paypal.com"
ORDERS = f"{BASE}/v2/checkout/orders"
SEARCH = f"{BASE}/v1/reporting/transactions"
START, END = datetime(2026, 10, 1, tzinfo=UTC), datetime(2026, 10, 31, tzinfo=UTC)


def not_json(status: int = 200) -> httpx.Response:
    return httpx.Response(status, content=b"<html>maintenance</html>")


@pytest.fixture
def gateway(monkeypatch: pytest.MonkeyPatch) -> HttpPayPalGateway:
    monkeypatch.setattr("app.common.http_client.time.sleep", lambda _s: None)
    respx.post(f"{BASE}/v1/oauth2/token").mock(
        return_value=httpx.Response(200, json={"access_token": "t", "expires_in": 3600})
    )
    client = make_client(BASE)
    return HttpPayPalGateway(client, TokenCache(client, "id", "secret"))


def unprocessable(issue: str | None) -> httpx.Response:
    details = [{"issue": issue, "description": "x"}] if issue else []
    return httpx.Response(422, json={"name": "UNPROCESSABLE_ENTITY", "details": details})


@respx.mock
def test_search_with_non_json_body_is_rejected(gateway: HttpPayPalGateway) -> None:
    respx.get(SEARCH).mock(return_value=not_json())
    with pytest.raises(PayPalError) as error:
        gateway.search_transactions(START, END, 1)
    assert error.value.code == "PAYPAL_REJECTED"


@respx.mock
def test_create_order_with_non_json_body_is_rejected(gateway: HttpPayPalGateway) -> None:
    respx.post(ORDERS).mock(return_value=not_json(201))
    with pytest.raises(PayPalError) as error:
        gateway.create_order("50.00", "USD", None)
    assert error.value.code == "PAYPAL_REJECTED"


@respx.mock
def test_create_order_without_id_is_rejected(gateway: HttpPayPalGateway) -> None:
    respx.post(ORDERS).mock(return_value=httpx.Response(201, json={"status": "CREATED"}))
    with pytest.raises(PayPalError) as error:
        gateway.create_order("50.00", "USD", None)
    assert error.value.code == "PAYPAL_REJECTED"


@respx.mock
def test_capture_with_non_json_body_is_rejected(gateway: HttpPayPalGateway) -> None:
    respx.post(f"{ORDERS}/ORDER1/capture").mock(return_value=not_json(201))
    with pytest.raises(PayPalError) as error:
        gateway.capture_order("ORDER1")
    assert error.value.code == "PAYPAL_REJECTED"


@respx.mock
def test_already_captured_order_says_it_was_paid(gateway: HttpPayPalGateway) -> None:
    respx.post(f"{ORDERS}/ORDER1/capture").mock(
        return_value=unprocessable("ORDER_ALREADY_CAPTURED")
    )
    with pytest.raises(PaymentDeclinedError) as error:
        gateway.capture_order("ORDER1")
    assert error.value.code == "ORDER_ALREADY_CAPTURED"
    assert error.value.message == ALREADY_CAPTURED_MESSAGE
    assert "No payment was made" not in error.value.message


@pytest.mark.parametrize(
    "response",
    [
        unprocessable("INSTRUMENT_DECLINED"),
        unprocessable(None),
        httpx.Response(422, content=b"not json"),
        httpx.Response(422, json=["ORDER_ALREADY_CAPTURED"]),
    ],
)
@respx.mock
def test_other_unprocessable_captures_stay_declined(
    gateway: HttpPayPalGateway, response: httpx.Response
) -> None:
    respx.post(f"{ORDERS}/ORDER1/capture").mock(return_value=response)
    with pytest.raises(PaymentDeclinedError) as error:
        gateway.capture_order("ORDER1")
    assert (error.value.code, error.value.message) == ("PAYMENT_DECLINED", DECLINED_MESSAGE)
