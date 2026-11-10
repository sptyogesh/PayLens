"""Fake Orders v2 for tests and E2E: amount 13.13 is declined, everything else captures."""

import itertools
from datetime import datetime
from typing import Any

from app.common.errors import NotFoundError
from app.paypal.orders_api import CaptureResult, parse_capture
from app.paypal.transactions_api import paypal_date

DECLINED_AMOUNT = "13.13"
FAKE_PAYER = {
    "email_address": "ava.us@example.com",
    "name": {"given_name": "Ava", "surname": "Stone"},
    "address": {"country_code": "US"},
}


def capture_payload(
    order_id: str, order: dict[str, str], capture_id: str, fee: str, when: datetime
) -> dict[str, Any]:
    currency, amount = order["currency"], order["amount"]
    status = "DECLINED" if amount == DECLINED_AMOUNT else "COMPLETED"
    breakdown = {
        "gross_amount": {"currency_code": currency, "value": amount},
        "paypal_fee": {"currency_code": currency, "value": fee},
    }
    capture = {
        "id": capture_id,
        "status": status,
        "amount": {"currency_code": currency, "value": amount},
        "seller_receivable_breakdown": breakdown,
        "create_time": paypal_date(when),
    }
    return {
        "id": order_id,
        "status": "COMPLETED",
        "purchase_units": [{"payments": {"captures": [capture]}}],
        "payer": FAKE_PAYER,
    }


class FakeOrders:
    """In-memory orders keyed by ID."""

    def __init__(self) -> None:
        self.orders: dict[str, dict[str, str]] = {}
        self._ids = itertools.count(1)

    def create(self, amount: str, currency: str) -> str:
        order_id = f"FAKEORDER{next(self._ids):08d}"
        self.orders[order_id] = {"amount": amount, "currency": currency}
        return order_id

    def capture(self, order_id: str, fee: str, when: datetime) -> CaptureResult:
        order = self.orders.get(order_id)
        if order is None:
            raise NotFoundError("This PayPal order was not found. No payment was made.")
        capture_id = order_id.replace("FAKEORDER", "FAKECAPTURE")
        return parse_capture(capture_payload(order_id, order, capture_id, fee, when))
