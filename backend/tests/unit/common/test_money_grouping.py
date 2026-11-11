"""Display grouping for the CA report: commas only, en-IN for INR (005)."""

import pytest

from app.common.money import display_money, group_digits


@pytest.mark.parametrize(
    ("amount", "inr", "usd"),
    [
        ("0.00", "0.00", "0.00"),
        ("999.99", "999.99", "999.99"),
        ("1000.00", "1,000.00", "1,000.00"),
        ("123456.78", "1,23,456.78", "123,456.78"),
        ("-12345678.90", "-1,23,45,678.90", "-12,345,678.90"),
    ],
)
def test_group_digits(amount: str, inr: str, usd: str) -> None:
    assert group_digits(amount, "INR") == inr
    assert group_digits(amount, "USD") == usd


def test_display_money() -> None:
    assert display_money("168000.00", "INR") == "INR 1,68,000.00"
