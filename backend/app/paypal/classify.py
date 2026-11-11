"""Classify a PayPal event into a TransactionKind (research R2).

Income needs BOTH an incoming-payment event code AND a positive amount, so an unexpected
code is never silently counted as income.
"""

from decimal import Decimal

from app.common.constants import (
    CONVERSION_EVENT_PREFIX,
    FEE_EVENT_CODES,
    HOLD_EVENT_PREFIXES,
    INCOME_EVENT_CODES,
    REFUND_EVENT_CODES,
    REFUND_EVENT_PREFIX,
    WITHDRAWAL_EVENT_PREFIX,
)
from app.common.types import TransactionKind, TransactionStatus

PAYPAL_STATUS = {
    "S": TransactionStatus.COMPLETED,
    "P": TransactionStatus.PENDING,
    "D": TransactionStatus.DENIED,
    "V": TransactionStatus.REVERSED,
}
INCOME_STATUSES = frozenset({TransactionStatus.COMPLETED, TransactionStatus.PENDING})


PREFIX_KINDS: tuple[tuple[tuple[str, ...], TransactionKind], ...] = (
    ((REFUND_EVENT_PREFIX,), TransactionKind.REFUND),
    ((WITHDRAWAL_EVENT_PREFIX,), TransactionKind.WITHDRAWAL),
    ((CONVERSION_EVENT_PREFIX,), TransactionKind.CONVERSION),
    (HOLD_EVENT_PREFIXES, TransactionKind.HOLD),
)


def classify(event_code: str | None, amount: Decimal) -> TransactionKind:
    if event_code is None:
        return TransactionKind.OTHER
    if event_code in INCOME_EVENT_CODES:
        return TransactionKind.INCOME if amount > 0 else TransactionKind.OUTGOING_PAYMENT
    if event_code in FEE_EVENT_CODES:
        return TransactionKind.FEE
    if event_code in REFUND_EVENT_CODES:
        return TransactionKind.REFUND
    for prefixes, kind in PREFIX_KINDS:
        if event_code.startswith(prefixes):
            return kind
    return TransactionKind.OTHER


def map_status(code: str | None) -> TransactionStatus | None:
    """PayPal S/P/D/V → our status. None when PayPal sends something unknown."""
    return PAYPAL_STATUS.get(code or "")


def counts_as_income(kind: TransactionKind, status: TransactionStatus) -> bool:
    return kind is TransactionKind.INCOME and status in INCOME_STATUSES
