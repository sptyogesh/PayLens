import json
from typing import Any

import httpx
import pytest
import respx

from app.common.errors import NotFoundError, PaymentDeclinedError, PayPalError
from app.common.http_client import make_client
from app.paypal import HttpPayPalGateway, TokenCache
from tests.fixtures.paypal.orders import capture_response

BASE = "https://api-m.sandbox.paypal.com"
ORDERS = f"{BASE}/v2/checkout/orders"


@pytest.fixture
def gateway(monkeypatch: pytest.MonkeyPatch) -> HttpPayPalGateway:
    monkeypatch.setattr("app.common.http_client.time.sleep", lambda _s: None)
    respx.post(f"{BASE}/v1/oauth2/token").mock(
        return_value=httpx.Response(200, json={"access_token": "t", "expires_in": 3600})
    )
    client = make_client(BASE)
    return HttpPayPalGateway(client, TokenCache(client, "id", "secret"))


@respx.mock
def test_create_order_body_and_same_request_id_on_retry(gateway: HttpPayPalGateway) -> None:
    route = respx.post(ORDERS).mock(
        side_effect=[
            httpx.Response(503),
            httpx.Response(201, json={"id": "ORDER1", "status": "CREATED"}),
        ]
    )
    assert gateway.create_order("50.00", "USD", "Logo design") == "ORDER1"
    first, second = (call.request for call in route.calls)
    assert first.headers["PayPal-Request-Id"] == second.headers["PayPal-Request-Id"]
    body: dict[str, Any] = json.loads(first.content)
    assert body == {
        "intent": "CAPTURE",
        "purchase_units": [
            {"amount": {"currency_code": "USD", "value": "50.00"}, "description": "Logo design"}
        ],
    }


@respx.mock
def test_capture_asks_for_full_representation(gateway: HttpPayPalGateway) -> None:
    route = respx.post(f"{ORDERS}/ORDER1/capture").mock(
        return_value=httpx.Response(201, json=capture_response())
    )
    result = gateway.capture_order("ORDER1")
    assert route.calls[0].request.headers["Prefer"] == "return=representation"
    assert "PayPal-Request-Id" in route.calls[0].request.headers
    capture = result.response.first_capture()
    assert capture is not None and capture.id == "3C679366HH908993F"


@pytest.mark.parametrize(
    ("response", "error"),
    [
        (httpx.Response(422, json={"name": "UNPROCESSABLE_ENTITY"}), PaymentDeclinedError),
        (httpx.Response(404, json={"name": "RESOURCE_NOT_FOUND"}), NotFoundError),
        (httpx.Response(400, json={"name": "INVALID_REQUEST"}), PayPalError),
        (httpx.Response(201, json=capture_response(status="DECLINED")), PaymentDeclinedError),
    ],
)
@respx.mock
def test_capture_failures_map_to_safe_errors(
    gateway: HttpPayPalGateway, response: httpx.Response, error: type[Exception]
) -> None:
    respx.post(f"{ORDERS}/ORDER1/capture").mock(return_value=response)
    with pytest.raises(error):
        gateway.capture_order("ORDER1")
