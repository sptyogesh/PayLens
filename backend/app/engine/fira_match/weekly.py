"""Weekly sum-match (FR-006): one FIRA may cover all payments of one ISO week."""

from collections.abc import Iterable
from decimal import Decimal

from app.common.constants import FIRA_AMOUNT_TOLERANCE_PCT, FIRA_WEEKLY_MIN_PAYMENTS
from app.engine.fira_match.score import within_pct
from app.engine.fira_match.types import FiraCandidate, PaymentCandidate


def weekly_match(
    fira: FiraCandidate, free_payments: Iterable[PaymentCandidate]
) -> list[str] | None:
    """Keys (sorted) of the same-currency payments in the FIRA's ISO week when their gross sum is
    within the amount tolerance of the FIRA amount and there are at least two; otherwise None."""
    week = fira.date.isocalendar()[:2]
    same_week = [
        payment
        for payment in free_payments
        if payment.currency == fira.currency and payment.date.isocalendar()[:2] == week
    ]
    if len(same_week) < FIRA_WEEKLY_MIN_PAYMENTS:
        return None
    total = sum((payment.gross for payment in same_week), Decimal(0))
    if not within_pct(fira.amount, total, FIRA_AMOUNT_TOLERANCE_PCT):
        return None
    return sorted(payment.payment_key for payment in same_week)
