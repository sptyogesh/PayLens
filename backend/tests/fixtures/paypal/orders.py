"""Builders for Orders v2 capture JSON in PayPal's format."""

from typing import Any, Final, TypedDict, Unpack


class CaptureFields(TypedDict, total=False):
    """Keyword overrides for `capture_response`; a field left out keeps its default."""

    capture_id: str
    status: str
    gross: str
    fee: str | None
    net: str | None
    currency: str
    email: str | None


CAPTURE_DEFAULTS: Final[CaptureFields] = {
    "capture_id": "3C679366HH908993F",
    "status": "COMPLETED",
    "gross": "100.00",
    "fee": "3.98",
    "net": "96.02",
    "currency": "USD",
    "email": "ava.us@example.com",
}


def breakdown(fields: CaptureFields) -> dict[str, Any]:
    currency = fields["currency"]
    result: dict[str, Any] = {"gross_amount": {"currency_code": currency, "value": fields["gross"]}}
    if fields["fee"] is not None:
        result["paypal_fee"] = {"currency_code": currency, "value": fields["fee"]}
    if fields["net"] is not None:
        result["net_amount"] = {"currency_code": currency, "value": fields["net"]}
    return result


def capture_response(**overrides: Unpack[CaptureFields]) -> dict[str, Any]:
    fields: CaptureFields = {**CAPTURE_DEFAULTS, **overrides}
    capture = {
        "id": fields["capture_id"],
        "status": fields["status"],
        "amount": {"currency_code": fields["currency"], "value": fields["gross"]},
        "seller_receivable_breakdown": breakdown(fields),
        "create_time": "2026-11-10T06:30:00Z",
    }
    payer: dict[str, Any] = {"name": {"given_name": "Ava", "surname": "Stone"}}
    if fields["email"]:
        payer["email_address"] = fields["email"]
    return {
        "id": "5O190127TN364715T",
        "status": "COMPLETED",
        "purchase_units": [{"payments": {"captures": [capture]}}],
        "payer": payer,
    }
