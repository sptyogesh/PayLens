"""Deterministic fake PayPal for tests and E2E (APP_ENV=test only, enforced in Settings).

Search returns 12 events in the last 30 days: 10 incoming payments and 2 non-income
events (a withdrawal and a refund), over 2 pages, in PayPal's own JSON format.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from app.common.dates import utc_now
from app.common.money import parse_money, round_money, to_api_string
from app.paypal.dto import SearchPage
from app.paypal.transactions_api import parse_page, paypal_date

FAKE_PAGE_SIZE = 6
FAKE_FEE_RATE = Decimal("0.044")
FAKE_FEE_FIXED = Decimal("0.30")
FAKE_CLIENTS = (
    ("ava.us@example.com", "Ava", "Stone", "US", "USD"),
    ("ben.uk@example.com", "Ben", "Hart", "GB", "GBP"),
    ("clara.de@example.com", "Clara", "Vogel", "DE", "EUR"),
    ("dan.au@example.com", "Dan", "Reid", "AU", "AUD"),
)


def fake_fee(amount: str) -> str:
    return to_api_string(round_money(abs(parse_money(amount)) * FAKE_FEE_RATE + FAKE_FEE_FIXED))


def fake_event(index: int, when: datetime, code: str, amount: str) -> dict[str, Any]:
    email, given, surname, country, currency = FAKE_CLIENTS[index % len(FAKE_CLIENTS)]
    fee = f"-{fake_fee(amount)}" if code.startswith("T00") else None
    info: dict[str, Any] = {
        "transaction_id": f"FAKE{index:013d}",
        "transaction_event_code": code,
        "transaction_initiation_date": paypal_date(when),
        "transaction_amount": {"currency_code": currency, "value": amount},
        "transaction_status": "S",
    }
    if fee is not None:
        info["fee_amount"] = {"currency_code": currency, "value": fee}
    payer = {
        "email_address": email,
        "country_code": country,
        "payer_name": {"given_name": given, "surname": surname},
    }
    return {"transaction_info": info, "payer_info": payer}


def build_events(now: datetime) -> list[dict[str, Any]]:
    events = [
        fake_event(i, now - timedelta(days=2 + i * 2), "T0006", f"{150 + i * 25}.00")
        for i in range(10)
    ]
    events.append(fake_event(10, now - timedelta(days=5), "T0400", "-200.00"))
    events.append(fake_event(11, now - timedelta(days=7), "T1107", "-25.00"))
    return events


class FakePayPalGateway:
    """In-memory stand-in for HttpPayPalGateway."""

    def __init__(self, now: datetime | None = None) -> None:
        self.events = build_events(now or utc_now())

    def search_transactions(self, start: datetime, end: datetime, page: int) -> SearchPage:
        in_window = [e for e in self.events if start <= self._when(e) < end]
        total_pages = (len(in_window) + FAKE_PAGE_SIZE - 1) // FAKE_PAGE_SIZE
        chunk = in_window[(page - 1) * FAKE_PAGE_SIZE : page * FAKE_PAGE_SIZE]
        return parse_page({"transaction_details": chunk, "page": page, "total_pages": total_pages})

    @staticmethod
    def _when(event: dict[str, Any]) -> datetime:
        raw = event["transaction_info"]["transaction_initiation_date"]
        return datetime.fromisoformat(raw.replace("Z", "+00:00"))
