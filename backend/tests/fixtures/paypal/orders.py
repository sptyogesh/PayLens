"""Builders for Orders v2 capture JSON in PayPal's format."""

from typing import Any


def capture_response(
    *,
    capture_id: str = "3C679366HH908993F",
    status: str = "COMPLETED",
    gross: str = "100.00",
    fee: str | None = "3.98",
    net: str | None = "96.02",
    currency: str = "USD",
    email: str | None = "ava.us@example.com",
) -> dict[str, Any]:
    breakdown: dict[str, Any] = {"gross_amount": {"currency_code": currency, "value": gross}}
    if fee is not None:
        breakdown["paypal_fee"] = {"currency_code": currency, "value": fee}
    if net is not None:
        breakdown["net_amount"] = {"currency_code": currency, "value": net}
    capture = {
        "id": capture_id,
        "status": status,
        "amount": {"currency_code": currency, "value": gross},
        "seller_receivable_breakdown": breakdown,
        "create_time": "2026-11-10T06:30:00Z",
    }
    payer: dict[str, Any] = {"name": {"given_name": "Ava", "surname": "Stone"}}
    if email:
        payer["email_address"] = email
    return {
        "id": "5O190127TN364715T",
        "status": "COMPLETED",
        "purchase_units": [{"payments": {"captures": [capture]}}],
        "payer": payer,
    }
