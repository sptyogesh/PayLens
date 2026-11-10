"""Score one (FIRA, payment) pair: reference +60, amount within 1% +25, date within 7 days +15."""

from decimal import Decimal
from typing import Final

from app.common.constants import (
    FIRA_AMOUNT_TOLERANCE_PCT,
    FIRA_DATE_WINDOW_DAYS,
    FIRA_MATCHED_MIN,
    FIRA_REVIEW_MIN,
    FIRA_SCORE_AMOUNT,
    FIRA_SCORE_DATE,
    FIRA_SCORE_REFERENCE,
    PERCENT_FACTOR,
)
from app.engine.fira_match.types import (
    REASON_AMOUNT,
    REASON_DATE,
    REASON_REFERENCE,
    REASON_SEPARATOR,
    FiraCandidate,
    FiraStatus,
    PaymentCandidate,
    ScoreBreakdown,
)

ZERO_SCORE: Final = ScoreBreakdown(reference=False, amount=False, date=False, total=0)


def within_pct(value: Decimal, base: Decimal, pct: Decimal) -> bool:
    """True when `value` is within `pct` percent of `base` (base > 0). Exact Decimal maths."""
    return abs(value - base) * PERCENT_FACTOR <= pct * base


def _normalise(reference: str | None) -> str:
    return "".join((reference or "").split()).casefold()


def reference_equal(fira_reference: str | None, transaction_id: str) -> bool:
    """Case- and space-insensitive compare; both sides must be non-empty."""
    left, right = _normalise(fira_reference), _normalise(transaction_id)
    return bool(left) and left == right


def score_pair(fira: FiraCandidate, payment: PaymentCandidate) -> ScoreBreakdown:
    """Score one pair. A currency mismatch scores 0 with every check False (F10)."""
    if fira.currency != payment.currency:
        return ZERO_SCORE
    reference = reference_equal(fira.reference, payment.paypal_transaction_id)
    amount = within_pct(fira.amount, payment.gross, FIRA_AMOUNT_TOLERANCE_PCT)
    in_window = abs((fira.date - payment.date).days) <= FIRA_DATE_WINDOW_DAYS
    total = (
        FIRA_SCORE_REFERENCE * reference + FIRA_SCORE_AMOUNT * amount + FIRA_SCORE_DATE * in_window
    )
    return ScoreBreakdown(reference=reference, amount=amount, date=in_window, total=total)


def status_for(score: int) -> FiraStatus:
    """>= 80 matched, 50-79 needs review, below 50 no match."""
    if score >= FIRA_MATCHED_MIN:
        return "matched"
    if score >= FIRA_REVIEW_MIN:
        return "needs_review"
    return "no_match"


def failed_reason(breakdown: ScoreBreakdown) -> str | None:
    """Plain reason listing each check that failed, or None when all passed."""
    parts = [
        text
        for passed, text in (
            (breakdown.reference, REASON_REFERENCE),
            (breakdown.amount, REASON_AMOUNT),
            (breakdown.date, REASON_DATE),
        )
        if not passed
    ]
    return REASON_SEPARATOR.join(parts) or None
