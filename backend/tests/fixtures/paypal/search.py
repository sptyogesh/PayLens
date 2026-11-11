"""Builders for Transaction Search JSON in PayPal's format (research R2–R6)."""

from typing import Any, Final, TypedDict, Unpack


class RowFields(TypedDict, total=False):
    """Keyword overrides for `row`; a field left out keeps its value from ROW_DEFAULTS."""

    amount: str
    fee: str | None
    code: str
    status: str
    email: str | None
    date: str
    currency: str


ROW_DEFAULTS: Final[RowFields] = {
    "amount": "100.00",
    "fee": "-3.98",
    "code": "T0006",
    "status": "S",
    "email": "client.us@example.com",
    "date": "2026-11-01T10:00:00+0000",
    "currency": "USD",
}


def row(tx_id: str, **overrides: Unpack[RowFields]) -> dict[str, Any]:
    fields: RowFields = {**ROW_DEFAULTS, **overrides}
    currency = fields["currency"]
    info: dict[str, Any] = {
        "transaction_id": tx_id,
        "transaction_event_code": fields["code"],
        "transaction_initiation_date": fields["date"],
        "transaction_amount": {"currency_code": currency, "value": fields["amount"]},
        "transaction_status": fields["status"],
    }
    if fields["fee"] is not None:
        info["fee_amount"] = {"currency_code": currency, "value": fields["fee"]}
    payer: dict[str, Any] = {
        "country_code": "US",
        "payer_name": {"given_name": "Ava", "surname": "Client"},
    }
    if fields["email"] is not None:
        payer["email_address"] = fields["email"]
    return {"transaction_info": info, "payer_info": payer}


def page(rows: list[dict[str, Any]], number: int = 1, total_pages: int = 1) -> dict[str, Any]:
    return {
        "transaction_details": rows,
        "page": number,
        "total_pages": total_pages,
        "total_items": len(rows),
    }
