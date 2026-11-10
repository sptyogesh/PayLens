from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.common.types import Money
from app.schemas import MoneyOut


def test_money_out_is_a_two_place_string() -> None:
    out = MoneyOut.of(Decimal("96.0249"), "USD")
    assert out.model_dump() == {"amount": "96.02", "currency": "USD"}
    assert MoneyOut.from_money(Money(amount=Decimal(5), currency="GBP")).amount == "5.00"


def test_money_out_rejects_numbers_and_bad_strings() -> None:
    for bad in [12.5, "12.5", "abc"]:
        with pytest.raises(ValidationError):
            MoneyOut(amount=bad, currency="USD")  # type: ignore[arg-type]
