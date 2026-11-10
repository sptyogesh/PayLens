"""Orders v2: create and capture on the server (FR-032, research R7).

Both calls send a PayPal-Request-Id that stays the same across retries (idempotency), and
capture asks for the full representation so the fee breakdown is returned (research R3).
"""

import json
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

import httpx
from pydantic import ValidationError

from app.common.errors import NotFoundError, PaymentDeclinedError, PayPalError
from app.paypal.schemas_orders import CaptureResponse, CreateOrderResponse

ORDERS_PATH = "/v2/checkout/orders"
DECLINED_MESSAGE = "PayPal did not approve this payment. No payment was made."
ORDER_NOT_FOUND_MESSAGE = "This PayPal order was not found. No payment was made."
REJECTED_MESSAGE = "PayPal could not process this checkout request. No payment was made."
CAPTURE_OK_STATUSES = frozenset({"COMPLETED", "PENDING"})

Request = Callable[..., httpx.Response]


@dataclass(frozen=True)
class CaptureResult:
    response: CaptureResponse
    raw: dict[str, Any]


def order_body(amount: str, currency: str, description: str | None) -> dict[str, Any]:
    unit: dict[str, Any] = {"amount": {"currency_code": currency, "value": amount}}
    if description:
        unit["description"] = description
    return {"intent": "CAPTURE", "purchase_units": [unit]}


def raise_for_checkout(response: httpx.Response) -> None:
    if response.status_code in {httpx.codes.OK, httpx.codes.CREATED}:
        return
    if response.status_code == httpx.codes.UNPROCESSABLE_ENTITY:
        raise PaymentDeclinedError(DECLINED_MESSAGE)
    if response.status_code == httpx.codes.NOT_FOUND:
        raise NotFoundError(ORDER_NOT_FOUND_MESSAGE)
    raise PayPalError(REJECTED_MESSAGE, code="PAYPAL_REJECTED")


def create_order(request: Request, amount: str, currency: str, description: str | None) -> str:
    response = request(
        "POST",
        ORDERS_PATH,
        json=order_body(amount, currency, description),
        headers={"PayPal-Request-Id": str(uuid.uuid4())},
    )
    raise_for_checkout(response)
    return CreateOrderResponse.model_validate_json(response.content).id


def parse_capture(payload: dict[str, Any]) -> CaptureResult:
    try:
        parsed = CaptureResponse.model_validate(payload)
    except ValidationError as error:
        raise PayPalError(REJECTED_MESSAGE, code="PAYPAL_REJECTED") from error
    capture = parsed.first_capture()
    if capture is None or capture.status not in CAPTURE_OK_STATUSES:
        raise PaymentDeclinedError(DECLINED_MESSAGE)
    return CaptureResult(response=parsed, raw=payload)


def capture_order(request: Request, order_id: str) -> CaptureResult:
    response = request(
        "POST",
        f"{ORDERS_PATH}/{order_id}/capture",
        json={},
        headers={"PayPal-Request-Id": str(uuid.uuid4()), "Prefer": "return=representation"},
    )
    raise_for_checkout(response)
    return parse_capture(json.loads(response.content))
