"""Required test case F12 (constitution): weekly sum-match.

Weekly FIRAs carry no reference; every date counts from MONDAY.
"""

from datetime import date

from app.engine.fira_match import REASON_WEEKLY, match_all, weekly_match
from tests.fixtures.fira_match import fira, pay

MONDAY = date(2026, 11, 2)  # ISO week 2026-W45 runs Mon 2 Nov to Sun 8 Nov

WEEK = [
    pay("p3", gross="300.00", start=MONDAY, days=6),
    pay("p1", gross="500.00", start=MONDAY),
    pay("p2", gross="200.00", start=MONDAY, days=3),
]


def test_f12_weekly_total_links_all_payments_of_the_week() -> None:
    next_week = fira("f1", amount="1009.00", start=MONDAY, days=9, reference=None)
    result = match_all([next_week], WEEK)
    same_week = fira("w", amount="1009.00", start=MONDAY, reference=None)
    assert weekly_match(same_week, WEEK) == ["p1", "p2", "p3"]
    # FIRA dated the following week: no weekly match, payments stay missing.
    assert result.firas[0].status == "no_match"

    result = match_all([fira("f1", amount="1009.00", start=MONDAY, reference=None)], WEEK)
    outcome = result.firas[0]
    assert outcome.status == "needs_review"
    assert outcome.kind == "weekly"
    assert outcome.reason == REASON_WEEKLY
    assert outcome.payment_keys == ["p1", "p2", "p3"]
    assert result.payments == {"p1": "needs_review", "p2": "needs_review", "p3": "needs_review"}


def test_weekly_sum_outside_one_percent_is_none() -> None:
    assert weekly_match(fira("f", amount="1010.10", start=MONDAY, reference=None), WEEK) is None
    assert weekly_match(fira("f", amount="989.99", start=MONDAY, reference=None), WEEK) is None


def test_weekly_needs_at_least_two_payments() -> None:
    single = [pay("p1", gross="500.00", start=MONDAY)]
    assert weekly_match(fira("f", amount="500.00", start=MONDAY, reference=None), single) is None


def test_weekly_ignores_other_week_and_currency() -> None:
    payments = [
        pay("p1", gross="500.00", start=MONDAY),
        pay("p2", gross="200.00", start=MONDAY, days=3),
        pay("p_prev", gross="999.00", start=MONDAY, days=-1),  # Sunday of the previous ISO week
        pay("p_eur", gross="999.00", start=MONDAY, days=2, currency="EUR"),
    ]
    found = weekly_match(fira("f", amount="700.00", start=MONDAY, reference=None), payments)
    assert found == ["p1", "p2"]


def test_weekly_payments_are_not_reused_by_a_later_fira() -> None:
    first = fira("f1", start=MONDAY, reference=None)
    second = fira("f2", start=MONDAY, reference=None, order=1)
    result = match_all([first, second], WEEK)
    assert [o.status for o in result.firas] == ["needs_review", "no_match"]
    assert result.firas[1].payment_keys == []
