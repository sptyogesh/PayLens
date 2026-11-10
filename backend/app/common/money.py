"""Decimal money helpers. Rounding happens only here, at the end (Principle III)."""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from app.common.constants import MONEY_PLACES


def parse_money(value: str) -> Decimal:
    """Parse a decimal string. Floats, NaN and infinities are rejected."""
    if not isinstance(value, str):
        raise TypeError("money must be parsed from a string, never a float")
    try:
        amount = Decimal(value.strip())
    except InvalidOperation as error:
        raise ValueError(f"not a decimal amount: {value!r}") from error
    if not amount.is_finite():
        raise ValueError(f"not a finite amount: {value!r}")
    return amount


def round_money(amount: Decimal) -> Decimal:
    """Round to 2 decimal places with ROUND_HALF_UP."""
    return amount.quantize(MONEY_PLACES, rounding=ROUND_HALF_UP)


def to_api_string(amount: Decimal) -> str:
    """Format for JSON: always a string with exactly 2 decimal places."""
    return format(round_money(amount), "f")
