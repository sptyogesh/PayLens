"""Builders for Transaction Search JSON in PayPal's format (research R2–R6)."""

from typing import Any


def row(
    tx_id: str,
    *,
    amount: str = "100.00",
    fee: str | None = "-3.98",
    code: str = "T0006",
    status: str = "S",
    email: str | None = "client.us@example.com",
    date: str = "2026-11-01T10:00:00+0000",
    currency: str = "USD",
) -> dict[str, Any]:
    info: dict[str, Any] = {
        "transaction_id": tx_id,
        "transaction_event_code": code,
        "transaction_initiation_date": date,
        "transaction_amount": {"currency_code": currency, "value": amount},
        "transaction_status": status,
    }
    if fee is not None:
        info["fee_amount"] = {"currency_code": currency, "value": fee}
    payer: dict[str, Any] = {
        "country_code": "US",
        "payer_name": {"given_name": "Ava", "surname": "Client"},
    }
    if email is not None:
        payer["email_address"] = email
    return {"transaction_info": info, "payer_info": payer}


def page(rows: list[dict[str, Any]], number: int = 1, total_pages: int = 1) -> dict[str, Any]:
    return {
        "transaction_details": rows,
        "page": number,
        "total_pages": total_pages,
        "total_items": len(rows),
    }
