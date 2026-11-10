from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.common.money import parse_money, round_money, to_api_string

amounts = st.decimals(min_value=-(10**9), max_value=10**9, allow_nan=False, allow_infinity=False)


@pytest.mark.parametrize(
    ("value", "expected"),
    [("1.005", "1.01"), ("1.004", "1.00"), ("-1.005", "-1.01"), ("2.675", "2.68"), ("0", "0.00")],
)
def test_round_money_is_half_up(value: str, expected: str) -> None:
    assert round_money(Decimal(value)) == Decimal(expected)


def test_parse_money_rejects_float_nan_and_text() -> None:
    with pytest.raises(TypeError):
        parse_money(1.5)  # type: ignore[arg-type]
    for bad in ["NaN", "Infinity", "abc", ""]:
        with pytest.raises(ValueError, match="amount"):
            parse_money(bad)


def test_to_api_string_always_has_two_places() -> None:
    assert to_api_string(Decimal("77914")) == "77914.00"
    assert to_api_string(Decimal("3.9")) == "3.90"
    assert to_api_string(Decimal("-0.5")) == "-0.50"


@given(amounts)
def test_api_string_round_trips(amount: Decimal) -> None:
    text = to_api_string(amount)
    assert parse_money(text) == round_money(amount)
    assert text.split(".")[1].__len__() == 2


@given(amounts)
def test_rounding_is_idempotent(amount: Decimal) -> None:
    assert round_money(round_money(amount)) == round_money(amount)
