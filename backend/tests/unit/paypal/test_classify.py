from decimal import Decimal

import pytest

from app.common.constants import INCOME_EVENT_CODES
from app.common.types import TransactionKind, TransactionStatus
from app.paypal.classify import classify, counts_as_income, map_status

POSITIVE, NEGATIVE = Decimal("10.00"), Decimal("-10.00")


@pytest.mark.parametrize("code", sorted(INCOME_EVENT_CODES))
def test_income_codes_with_positive_amount_are_income(code: str) -> None:
    assert classify(code, POSITIVE) is TransactionKind.INCOME


def test_income_code_with_negative_amount_is_outgoing() -> None:
    assert classify("T0000", NEGATIVE) is TransactionKind.OUTGOING_PAYMENT


@pytest.mark.parametrize(
    ("code", "kind"),
    [
        ("T0400", TransactionKind.WITHDRAWAL),
        ("T0403", TransactionKind.WITHDRAWAL),
        ("T1107", TransactionKind.REFUND),
        ("T1100", TransactionKind.REFUND),
        ("T1201", TransactionKind.REFUND),
        ("T0200", TransactionKind.CONVERSION),
        ("T1503", TransactionKind.HOLD),
        ("T2105", TransactionKind.HOLD),
        ("T0107", TransactionKind.FEE),
        ("T9999", TransactionKind.OTHER),
        (None, TransactionKind.OTHER),
    ],
)
def test_p8_non_payment_events_are_never_income(code: str | None, kind: TransactionKind) -> None:
    assert classify(code, POSITIVE) is kind


def test_status_mapping() -> None:
    assert [map_status(c) for c in "SPDV"] == [
        TransactionStatus.COMPLETED,
        TransactionStatus.PENDING,
        TransactionStatus.DENIED,
        TransactionStatus.REVERSED,
    ]
    assert map_status("X") is None
    assert map_status(None) is None


def test_only_completed_or_pending_income_counts() -> None:
    assert counts_as_income(TransactionKind.INCOME, TransactionStatus.COMPLETED)
    assert counts_as_income(TransactionKind.INCOME, TransactionStatus.PENDING)
    assert not counts_as_income(TransactionKind.INCOME, TransactionStatus.DENIED)
    assert not counts_as_income(TransactionKind.INCOME, TransactionStatus.REVERSED)
    assert not counts_as_income(TransactionKind.WITHDRAWAL, TransactionStatus.COMPLETED)
