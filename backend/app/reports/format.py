"""Display strings for the CA report. Values are copied from ReportData strings; no arithmetic.

Amounts get thousands commas only (en-IN for INR). A negative FX loss is shown as a gain by
dropping its minus sign and labelling it "gain".
"""

from typing import Final
from xml.sax.saxutils import escape

from app.common.money import display_money, group_digits
from app.schemas.common import MoneyOut

MINUS: Final = "-"
GAIN: Final = "gain"
NO_PERCENT: Final = "n/a"
RUPEE: Final = "₹"
RUPEE_TEXT: Final = "INR "  # the built-in PDF fonts have no ₹ glyph


PDF_TEXT_ENCODING: Final = "cp1252"  # what the built-in Helvetica fonts can draw


def money(value: MoneyOut) -> str:
    """'INR 1,23,456.78'."""
    return display_money(value.amount, value.currency)


def amount(value: MoneyOut) -> str:
    """'1,23,456.78' (for table cells whose header names the currency)."""
    return group_digits(value.amount, value.currency)


def is_gain(value: MoneyOut) -> bool:
    return value.amount.startswith(MINUS)


def without_sign(value: MoneyOut) -> MoneyOut:
    return value.model_copy(update={"amount": value.amount.removeprefix(MINUS)})


def fx_cell(value: MoneyOut) -> str:
    """FX loss in a table: '1,234.56', or '1,234.56 gain' when negative."""
    return f"{amount(without_sign(value))} {GAIN}" if is_gain(value) else amount(value)


def percent(value: str | None) -> str:
    return f"{value}%" if value is not None else NO_PERCENT


def text(value: str) -> str:
    """Escape user data (client names, AI text) for ReportLab's paragraph markup; "₹" is
    written "INR " because the built-in fonts cannot draw it."""
    printable = value.replace(RUPEE, RUPEE_TEXT).encode(PDF_TEXT_ENCODING, errors="replace")
    return escape(printable.decode(PDF_TEXT_ENCODING))


def is_printable(value: str) -> bool:
    """False when the built-in PDF fonts cannot show a character (it would print as "?")."""
    try:
        value.replace(RUPEE, RUPEE_TEXT).encode(PDF_TEXT_ENCODING)
    except UnicodeEncodeError:
        return False
    return True
