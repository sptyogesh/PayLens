from typing import get_args

import pytest
from fastapi.testclient import TestClient

from app.common.constants import CHECKOUT_CURRENCIES
from app.schemas.pay import CheckoutCurrency

VALID = {"amount": "50.00", "currency": "USD", "description": "Logo design"}


def test_create_then_capture_records_payment(api: TestClient) -> None:
    created = api.post("/pay/orders", json=VALID)
    assert created.status_code == 201
    order_id = created.json()["order_id"]
    captured = api.post(f"/pay/orders/{order_id}/capture")
    assert captured.status_code == 200
    body = captured.json()
    assert body["gross"] == {"amount": "50.00", "currency": "USD"}
    assert (body["order_id"], body["status"], body["recorded"]) == (order_id, "completed", True)
    items = api.get("/transactions").json()["items"]
    assert [i["paypal_transaction_id"] for i in items] == [body["transaction_id"]]
    assert items[0]["source"] == "paypal_sandbox"


@pytest.mark.parametrize(
    "overrides",
    [
        {"amount": ""},
        {"amount": "0"},
        {"amount": "-5.00"},
        {"amount": "1.234"},
        {"amount": "10000.01"},
        {"amount": 50},
        {"currency": "INR"},
        {"description": "x" * 128},
    ],
)
def test_invalid_orders_are_rejected(api: TestClient, overrides: dict[str, object]) -> None:
    response = api.post("/pay/orders", json={**VALID, **overrides})
    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_ERROR")


def test_max_amount_and_127_char_description_are_allowed(api: TestClient) -> None:
    body = {**VALID, "amount": "10000", "description": "x" * 127}
    assert api.post("/pay/orders", json=body).status_code == 201


def test_declined_capture_is_422_payment_declined(api: TestClient) -> None:
    order_id = api.post("/pay/orders", json={**VALID, "amount": "13.13"}).json()["order_id"]
    response = api.post(f"/pay/orders/{order_id}/capture")
    assert (response.status_code, response.json()["error"]["code"]) == (422, "PAYMENT_DECLINED")
    assert api.get("/transactions").json()["total"] == 0


def test_unknown_or_malformed_order_ids(api: TestClient) -> None:
    assert api.post("/pay/orders/NOPE1/capture").status_code == 404
    assert api.post("/pay/orders/bad..id/capture").status_code in {404, 422}


def test_eleventh_pay_request_in_a_minute_is_rate_limited(api: TestClient) -> None:
    statuses = [api.post("/pay/orders", json=VALID).status_code for _ in range(11)]
    assert statuses == [201] * 10 + [429]


def test_currency_list_matches_constant() -> None:
    assert get_args(CheckoutCurrency) == CHECKOUT_CURRENCIES
