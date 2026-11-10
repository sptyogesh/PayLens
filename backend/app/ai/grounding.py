"""Grounding check (FR-004, SC-003, research R2): every number in an answer must come from a tool.

Allowed numbers come only from numeric tool fields, figures, period labels, today's date and the
question — never from free text such as client names or group labels (a name can carry injected
numbers). Comparison is exact after normalising: commas removed (en-IN "1,26,678.93" equals
"126678.93") and trailing decimal zeros dropped ("7.30" equals "7.3"); no rounding is accepted.
A negative tool value (an FX gain) must be written with its minus sign or next to the word "gain".
Small integers (≤ GROUNDING_FREE_INTEGER_MAX, e.g. "3 months") are free unless they sit next to
"%", "₹" or a currency code, where they are amounts and must be grounded.
"""

import re
from collections.abc import Iterable
from typing import Any, Final

from app.ai.types import ToolResult
from app.common.constants import (
    GROUNDING_CONTEXT_CHARS,
    GROUNDING_FREE_INTEGER_MAX,
    GROUNDING_PREFIX_LOOKBACK,
    GROUNDING_SIGN_LOOKBACK,
    GROUNDING_TEXT_KEYS,
)

NUMBER: Final = re.compile(r"\d[\d,]*(?:\.\d+)?")
YEAR: Final = re.compile(r"^(19|20)\d\d$")
MINUS_SIGNS: Final = ("-", "−")
MONEY_PREFIX: Final = re.compile(r"(₹|\b[A-Z]{3})\s?[-−]?$")  # currency codes are upper case
RUPEE_WORD_PREFIX: Final = re.compile(r"\b(rs\.?|inr)\s?$", re.IGNORECASE)
# Words after a number that make it an amount ("12 lakh", "5 crore", "3k", "10 rupees").
AMOUNT_SUFFIX: Final = re.compile(
    r"^\s?(%|lakhs?|lacs?|crores?|cr\b|k\b|rupees?|inr\b)", re.IGNORECASE
)
GAIN_WORD: Final = "gain"
SHORT_YEAR: Final = 2


def normalise(token: str) -> str:
    text = token.replace(",", "").rstrip(".")
    whole, _, fraction = text.partition(".")
    whole = whole.lstrip("0") or "0"
    fraction = fraction.rstrip("0")
    return f"{whole}.{fraction}" if fraction else whole


def is_negative(text: str, start: int) -> bool:
    """A minus right before the number (or before its "₹"), not a hyphen inside a date."""
    before = text[max(0, start - GROUNDING_SIGN_LOOKBACK) : start]
    if before.endswith(("-₹", "−₹")):
        return True
    if not before.endswith(MINUS_SIGNS):
        return False
    lookback = GROUNDING_SIGN_LOOKBACK
    previous = text[start - lookback] if start >= lookback else " "
    return not previous.isalnum()


def signed_tokens(text: str) -> list[tuple[str, int, int]]:
    """(normalised signed value, start, end) for every number in `text`."""
    found: list[tuple[str, int, int]] = []
    for match in NUMBER.finditer(text):
        token = match.group().rstrip(",")
        value = normalise(token)
        if is_negative(text, match.start()) and value != "0":
            value = "-" + value
        found.append((value, match.start(), match.start() + len(token)))
    return found


def number_tokens(text: str) -> list[str]:
    return [value for value, _, _ in signed_tokens(text)]


def leaves(value: Any, key: str = "") -> Iterable[tuple[str, str]]:
    """(key, scalar as text) for every scalar inside a JSON-safe tool result."""
    if isinstance(value, dict):
        for child_key, item in value.items():
            yield from leaves(item, str(child_key))
    elif isinstance(value, list):
        for item in value:
            yield from leaves(item, key)
    elif value is not None and not isinstance(value, bool):
        yield key, str(value)


def tool_numbers(content: dict[str, Any]) -> set[str]:
    """Numbers of numeric fields; from free-text fields (client names, labels) only years."""
    found: set[str] = set()
    for key, text in leaves(content):
        values = number_tokens(text)
        found |= {v for v in values if YEAR.match(v)} if key in GROUNDING_TEXT_KEYS else set(values)
    return found


def with_years(values: set[str]) -> set[str]:
    """A year also allows the next year and both short forms ("FY 2026-27")."""
    extra: set[str] = set()
    for value in values:
        if YEAR.match(value):
            for year in (int(value), int(value) + 1):
                extra |= {str(year), str(year)[-SHORT_YEAR:]}
    return values | extra


def allowed_numbers(tool_results: list[ToolResult], question: str, periods: list[str]) -> set[str]:
    texts: list[str] = [question, *periods]
    allowed: set[str] = set()
    for result in tool_results:
        allowed |= tool_numbers(result.content)
        texts.append(result.period_label)
        texts.extend(figure.value for figure in result.figures)
    return with_years(allowed | {value for text in texts for value in number_tokens(text)})


def is_amount_context(text: str, start: int, end: int) -> bool:
    after = text[end : end + GROUNDING_CONTEXT_CHARS]
    before = text[max(0, start - GROUNDING_PREFIX_LOOKBACK) : start]
    prefix = MONEY_PREFIX.search(before) or RUPEE_WORD_PREFIX.search(before)
    return bool(AMOUNT_SUFFIX.match(after) or prefix)


def is_grounded(text: str, token: tuple[str, int, int], allowed: set[str]) -> bool:
    value, start, end = token
    if value in allowed:
        return True
    window = text[max(0, start - GROUNDING_CONTEXT_CHARS) : end + GROUNDING_CONTEXT_CHARS]
    if f"-{value}" in allowed and GAIN_WORD in window.lower():
        return True  # a negative FX loss written as a gain
    small = value.isdigit() and int(value) <= GROUNDING_FREE_INTEGER_MAX
    return small and not is_amount_context(text, start, end)


def ungrounded_numbers(answer: str, allowed: set[str]) -> list[str]:
    """Numbers in the answer that no numeric tool field, question or period label contains."""
    return [token[0] for token in signed_tokens(answer) if not is_grounded(answer, token, allowed)]


def allowed_from_content(content: dict[str, Any], texts: list[str]) -> set[str]:
    """Allowed numbers for one plain JSON object (e.g. the CA report data) plus extra texts."""
    found = tool_numbers(content) | {value for text in texts for value in number_tokens(text)}
    return with_years(found)
