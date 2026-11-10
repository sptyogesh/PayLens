"""Builders for FIRA matching engine tests (004): one FIRA and one payment candidate.

Dates are `start` plus `days`; a field left out keeps the default below.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Final, TypedDict, Unpack

from app.engine.fira_match import FiraCandidate, PaymentCandidate

DAY: Final = date(2026, 11, 4)


class FiraFields(TypedDict, total=False):
    amount: str
    start: date
    days: int
    reference: str | None
    order: int
    currency: str


class PayFields(TypedDict, total=False):
    gross: str
    start: date
    days: int
    txn: str
    currency: str


FIRA_DEFAULTS: Final[FiraFields] = {
    "amount": "1000.00",
    "start": DAY,
    "days": 0,
    "reference": "T1",
    "order": 0,
    "currency": "USD",
}
PAY_DEFAULTS: Final[PayFields] = {
    "gross": "1000.00",
    "start": DAY,
    "days": 0,
    "txn": "T1",
    "currency": "USD",
}


def fira(key: str = "f1", **overrides: Unpack[FiraFields]) -> FiraCandidate:
    fields: FiraFields = {**FIRA_DEFAULTS, **overrides}
    return FiraCandidate(
        fira_key=key,
        amount=Decimal(fields["amount"]),
        currency=fields["currency"],
        date=fields["start"] + timedelta(days=fields["days"]),
        reference=fields["reference"],
        order=fields["order"],
    )


def pay(key: str = "p1", **overrides: Unpack[PayFields]) -> PaymentCandidate:
    fields: PayFields = {**PAY_DEFAULTS, **overrides}
    return PaymentCandidate(
        payment_key=key,
        paypal_transaction_id=fields["txn"],
        gross=Decimal(fields["gross"]),
        currency=fields["currency"],
        date=fields["start"] + timedelta(days=fields["days"]),
    )
