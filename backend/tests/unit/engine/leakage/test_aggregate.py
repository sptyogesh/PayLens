"""Required test cases L11 (group sums) and L12 (multiple currencies)."""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.common.types import Money
from app.engine.leakage import (
    LeakageInput,
    LeakageResult,
    LeakageRow,
    by_client,
    by_currency,
    by_month,
    calculate_leakage,
    gross_by_currency,
    simulated_paypal_rate,
    totals,
)

D = Decimal
RATES = {"USD": D("84"), "GBP": D("106.5"), "EUR": D("90.25"), "AUD": D("55.1")}


def row(gross: str, currency: str = "USD", month: str = "2026-11", client: str = "a") -> LeakageRow:
    mid = RATES[currency]
    fee = (D(gross) * D("0.044")).quantize(D("0.01"))
    result = calculate_leakage(
        LeakageInput(
            gross=D(gross),
            fee=fee,
            currency=currency,
            mid_rate=mid,
            paypal_rate=simulated_paypal_rate(mid),
        )
    )
    assert isinstance(result, LeakageResult)
    return LeakageRow(month=month, client_key=client, client_label=client.upper(), result=result)


def test_l12_each_currency_uses_its_own_rate() -> None:
    rows = [row("100.00", c) for c in RATES]
    assert [r.result.ideal_inr for r in rows] == [
        D("8400.00"),
        D("10650.00"),
        D("9025.00"),
        D("5510.00"),
    ]
    assert totals(rows).income_inr == D("33585.00")


def test_l11_months_and_clients_sum_to_totals() -> None:
    rows = [
        row("100.00", "USD", "2026-09", "a"),
        row("250.50", "GBP", "2026-10", "b"),
        row("75.25", "EUR", "2026-10", "a"),
        row("999.99", "AUD", "2026-11", "c"),
    ]
    overall = totals(rows)
    for groups in (by_month(rows), by_client(rows)):
        for field in ("income_inr", "fee_loss_inr", "fx_loss_inr", "total_leakage_inr"):
            assert sum(getattr(g.totals, field) for g in groups) == getattr(overall, field)
        assert sum(g.totals.payment_count for g in groups) == overall.payment_count == 4


def test_sort_orders_and_labels() -> None:
    rows = [row("10.00", month="2026-09", client="a"), row("500.00", month="2026-11", client="b")]
    months = by_month(rows)
    assert [(m.key, m.label) for m in months] == [("2026-11", "Nov 2026"), ("2026-09", "Sep 2026")]
    assert [c.key for c in by_client(rows)] == ["b", "a"]


def test_percent_is_total_over_income() -> None:
    result = totals([row("1000.00")])
    expected = (result.total_leakage_inr / result.income_inr * 100).quantize(D("0.01"))
    assert result.leakage_percent == expected


def test_empty_rows_have_no_percent() -> None:
    empty = totals([])
    assert (empty.payment_count, empty.income_inr, empty.leakage_percent) == (0, D(0), None)


@given(st.lists(st.tuples(st.integers(1, 10**7), st.sampled_from(sorted(RATES))), max_size=20))
def test_l11_property_groups_always_add_up(values: list[tuple[int, str]]) -> None:
    rows = [
        row(str(D(c) / 100), cur, f"2026-{i % 3 + 9:02d}", str(i % 4))
        for i, (c, cur) in enumerate(values)
    ]
    overall = totals(rows)
    assert sum(g.totals.total_leakage_inr for g in by_month(rows)) == overall.total_leakage_inr
    assert sum(g.totals.total_leakage_inr for g in by_client(rows)) == overall.total_leakage_inr


def test_fx_gain_totals_stay_negative_and_cards_add_up() -> None:
    gain = calculate_leakage(
        LeakageInput(gross=D(100), fee=D(4), currency="USD", mid_rate=D(84), paypal_rate=D(85))
    )
    assert isinstance(gain, LeakageResult)
    result = totals([LeakageRow(month="2026-11", client_key="a", client_label="A", result=gain)])
    assert result.fx_loss_inr == D("-96.00")
    assert result.fee_loss_inr + result.fx_loss_inr == result.total_leakage_inr


@given(st.lists(st.tuples(st.integers(1, 10**7), st.sampled_from(sorted(RATES))), max_size=20))
def test_cards_always_add_up(values: list[tuple[int, str]]) -> None:
    overall = totals([row(str(D(c) / 100), cur) for c, cur in values])
    assert overall.fee_loss_inr + overall.fx_loss_inr == overall.total_leakage_inr


# --- 003: by currency (income_summary tool) ---


def with_gross(r: LeakageRow, gross: str, currency: str) -> LeakageRow:
    return r.model_copy(update={"gross": Money(amount=D(gross), currency=currency)})


def test_gross_is_summed_per_currency_never_mixed() -> None:
    rows = [
        with_gross(row("100.00"), "100.00", "USD"),
        with_gross(row("50.00", "GBP"), "50.00", "GBP"),
        with_gross(row("25.50"), "25.50", "USD"),
    ]
    assert gross_by_currency(rows) == [
        Money(amount=D("50.00"), currency="GBP"),
        Money(amount=D("125.50"), currency="USD"),
    ]
    groups = by_currency(rows)
    assert [(g.key, g.totals.payment_count) for g in groups] == [("GBP", 1), ("USD", 2)]
    assert sum(g.totals.income_inr for g in groups) == totals(rows).income_inr


def test_by_currency_needs_the_gross_amount() -> None:
    assert gross_by_currency([]) == []
    with pytest.raises(ValueError, match="gross"):
        by_currency([row("10.00")])
