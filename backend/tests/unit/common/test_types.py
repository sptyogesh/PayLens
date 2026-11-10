from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.common.types import Money, TransactionSource


def test_money_keeps_exact_decimal_and_currency() -> None:
    money = Money(amount=Decimal("77914.00"), currency="INR")
    assert money.amount == Decimal("77914.00")
    assert money.currency == "INR"


def test_money_accepts_decimal_string() -> None:
    # A decimal string is coerced by the validator; mypy only knows the Decimal field type.
    # Ignore on the next line: a string amount on purpose; the model must parse it to Decimal
    assert Money(amount="10.50", currency="USD").amount == Decimal("10.50")  # type: ignore[arg-type]


def test_money_rejects_float() -> None:
    with pytest.raises(ValidationError, match="float"):
        Money(amount=10.5, currency="USD")  # type: ignore[arg-type]  # deliberately wrong type


@pytest.mark.parametrize("currency", ["usd", "US", "USDX", "", "12A"])
def test_money_rejects_invalid_currency(currency: str) -> None:
    with pytest.raises(ValidationError):
        Money(amount=Decimal(1), currency=currency)


def test_source_values_match_api_labels() -> None:
    assert [s.value for s in TransactionSource] == ["paypal_sandbox", "demo_seed"]
