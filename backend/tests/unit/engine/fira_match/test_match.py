"""Required test cases F1-F5, F10, F11, F13 (constitution) for matching all FIRAs at once."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.common.constants import FIRA_MATCHED_MIN
from app.engine.fira_match import (
    REASON_AMOUNT,
    REASON_DATE,
    REASON_NO_CURRENCY,
    REASON_REFERENCE,
    REASON_TAKEN,
    match_all,
)
from tests.fixtures.fira_match import FiraFields, fira, pay


@pytest.mark.parametrize(
    ("kwargs", "score", "status", "payment", "reason"),
    [
        ({}, 100, "matched", "matched", None),  # F1
        ({"days": 10}, 85, "matched", "matched", None),  # F2
        ({"amount": "1030.00"}, 75, "needs_review", "needs_review", REASON_AMOUNT),  # F3
        (
            {"amount": "1030.00", "days": 9},
            60,
            "needs_review",
            "needs_review",
            f"{REASON_AMOUNT}; {REASON_DATE}",
        ),  # F4
        ({"reference": None}, 40, "no_match", "missing", REASON_REFERENCE),  # F5
    ],
)
def test_f1_to_f5_statuses(
    kwargs: FiraFields, score: int, status: str, payment: str, reason: str | None
) -> None:
    result = match_all([fira(**kwargs)], [pay(), pay("p2", gross="5000.00", days=1, txn="T2")])
    outcome = result.firas[0]
    assert (outcome.score, outcome.status, outcome.reason) == (score, status, reason)
    assert result.payments == {"p1": payment, "p2": "missing"}
    assert outcome.payment_keys == ([] if status == "no_match" else ["p1"])


def test_f10_currency_differs_is_no_match() -> None:
    result = match_all([fira(currency="EUR")], [pay()])
    outcome = result.firas[0]
    assert (outcome.status, outcome.score, outcome.reason) == ("no_match", 0, REASON_NO_CURRENCY)
    assert result.payments == {"p1": "missing"}


def test_f11_higher_score_keeps_the_payment() -> None:
    weaker = fira("f_weak", amount="1030.00", order=0)  # 75
    stronger = fira("f_strong", order=1)  # 100
    result = match_all([weaker, stronger], [pay()])
    weak, strong = result.firas
    assert (strong.status, strong.payment_keys) == ("matched", ["p1"])
    assert (weak.status, weak.reason, weak.payment_keys) == ("needs_review", REASON_TAKEN, [])
    assert weak.score == 75
    assert result.payments == {"p1": "matched"}


def test_f11_equal_scores_earlier_upload_wins() -> None:
    result = match_all([fira("f_late", order=5), fira("f_early", order=1)], [pay()])
    assert [o.status for o in result.firas] == ["needs_review", "matched"]


def test_f13_payment_without_fira_is_missing() -> None:
    result = match_all([], [pay("p2"), pay("p1")])
    assert result.firas == []
    assert list(result.payments.items()) == [("p1", "missing"), ("p2", "missing")]


def test_tie_break_prefers_closest_date_then_payment_key() -> None:
    near, far = pay("p_b", days=2, txn="X"), pay("p_a", days=-5, txn="X")
    no_ref = fira(reference="X")
    assert match_all([no_ref], [far, near]).firas[0].payment_keys == ["p_b"]
    twins = [pay("p_z", txn="X"), pay("p_y", txn="X")]
    assert match_all([no_ref], twins).firas[0].payment_keys == ["p_y"]


def test_output_is_deterministic_regardless_of_payment_order() -> None:
    firas = [fira("f1", reference="T1"), fira("f2", reference="T2", order=1)]
    payments = [pay("p1", txn="T1"), pay("p2", txn="T2")]
    assert match_all(firas, payments) == match_all(firas, list(reversed(payments)))


AMOUNTS = st.sampled_from(["1000.00", "1005.00", "1030.00", "2000.00"])
FIRAS = st.lists(
    st.tuples(AMOUNTS, st.integers(-10, 10), st.sampled_from([None, "T0", "T1", "T2"])),
    max_size=5,
)
PAYMENTS = st.lists(st.tuples(AMOUNTS, st.integers(-10, 10)), max_size=4)


@given(FIRAS, PAYMENTS)
def test_each_payment_linked_once_and_matched_scores_high(
    fira_specs: list[tuple[str, int, str | None]], payment_specs: list[tuple[str, int]]
) -> None:
    firas = [
        fira(f"f{i}", amount=amount, days=days, reference=ref, order=i)
        for i, (amount, days, ref) in enumerate(fira_specs)
    ]
    payments = [
        pay(f"p{i}", gross=gross, days=days, txn=f"T{i}")
        for i, (gross, days) in enumerate(payment_specs)
    ]
    result = match_all(firas, payments)
    linked = [key for outcome in result.firas for key in outcome.payment_keys]
    assert len(linked) == len(set(linked))
    for outcome in result.firas:
        if outcome.status == "matched":
            assert outcome.score is not None and outcome.score >= FIRA_MATCHED_MIN
    assert sorted(result.payments) == list(result.payments)
