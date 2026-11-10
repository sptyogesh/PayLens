"""Required test cases F1-F10 (constitution) for scoring one FIRA against one payment."""

from decimal import Decimal
from typing import Unpack

import pytest
from pydantic import ValidationError

from app.engine.fira_match import (
    REASON_AMOUNT,
    REASON_DATE,
    REASON_REFERENCE,
    FiraCandidate,
    PaymentCandidate,
    ScoreBreakdown,
    failed_reason,
    reference_equal,
    score_pair,
    status_for,
    within_pct,
)
from tests.fixtures.fira_match import DAY, FiraFields, fira

D = Decimal
TXN = "5TY05013RG002845M"


PAYMENT = PaymentCandidate(
    payment_key="p1", paypal_transaction_id=TXN, gross=D("1000.00"), currency="USD", date=DAY
)


def scored(**overrides: Unpack[FiraFields]) -> ScoreBreakdown:
    fields: FiraFields = {"reference": TXN, **overrides}
    return score_pair(fira(**fields), PAYMENT)


@pytest.mark.parametrize(
    ("kwargs", "total", "status"),
    [
        ({}, 100, "matched"),  # F1
        ({"days": 10}, 85, "matched"),  # F2
        ({"amount": "1030.00"}, 75, "needs_review"),  # F3
        ({"amount": "1030.00", "days": -10}, 60, "needs_review"),  # F4
        ({"reference": None}, 40, "no_match"),  # F5
    ],
)
def test_f1_to_f5_scores_and_status(kwargs: FiraFields, total: int, status: str) -> None:
    assert scored(**kwargs).total == total
    assert status_for(total) == status


@pytest.mark.parametrize("amount", ["1010.00", "990.00"])
def test_f6_exactly_one_percent_counts(amount: str) -> None:
    assert scored(amount=amount).amount is True


@pytest.mark.parametrize("amount", ["1010.10", "989.90"])
def test_f7_just_over_one_percent_does_not_count(amount: str) -> None:
    assert scored(amount=amount).amount is False


@pytest.mark.parametrize("days", [7, -7])
def test_f8_exactly_seven_days_counts(days: int) -> None:
    assert scored(days=days).date is True


@pytest.mark.parametrize("days", [8, -8])
def test_f9_eight_days_does_not_count(days: int) -> None:
    assert scored(days=days).date is False


def test_f10_currency_differs_scores_zero() -> None:
    result = scored(currency="EUR")
    assert result == ScoreBreakdown(reference=False, amount=False, date=False, total=0)
    assert status_for(result.total) == "no_match"


def test_status_boundaries() -> None:
    assert [status_for(s) for s in (80, 79, 50, 49)] == [
        "matched",
        "needs_review",
        "needs_review",
        "no_match",
    ]


def test_reference_compare_ignores_case_and_spaces() -> None:
    assert reference_equal("  5ty0 5013rg002845m ", TXN)
    assert scored(reference=" 5ty05013RG002845m\n").reference is True


@pytest.mark.parametrize("reference", [None, "", "   ", "OTHER"])
def test_reference_empty_or_different_does_not_match(reference: str | None) -> None:
    assert reference_equal(reference, TXN) is False
    assert reference_equal(reference, "") is False


def test_within_pct_is_exact_decimal() -> None:
    assert within_pct(D("101"), D("100"), D("1"))
    assert not within_pct(D("101.0001"), D("100"), D("1"))


def test_failed_reason_lists_each_failed_check() -> None:
    assert failed_reason(scored()) is None
    assert failed_reason(scored(reference=None, amount="2000.00", days=30)) == (
        f"{REASON_REFERENCE}; {REASON_AMOUNT}; {REASON_DATE}"
    )


def test_float_amounts_are_rejected() -> None:
    fields: dict[str, object] = {"currency": "USD", "date": DAY}
    with pytest.raises(ValidationError):
        FiraCandidate.model_validate(
            {**fields, "fira_key": "f", "amount": 1000.0, "reference": None, "order": 0}
        )
    with pytest.raises(ValidationError):
        PaymentCandidate.model_validate(
            {**fields, "payment_key": "p", "paypal_transaction_id": "t", "gross": 1000.0}
        )


@pytest.mark.parametrize("amount", ["0", "-1.00"])
def test_amount_must_be_positive(amount: str) -> None:
    with pytest.raises(ValidationError):
        fira(amount=amount)
