"""Answers written by code, not the LLM: no data, fallbacks, read-only, tax (FR-006, FR-007)."""

import re
from typing import Final

from app.common.constants import TAX_KEYWORDS

ANY_PERIOD: Final = "the selected period"
NO_DATA_TEMPLATE: Final = (
    "The data is not available for {periods}. No payments matched this question."
)
UNAVAILABLE_ANSWER: Final = (
    "The assistant is not available right now. Your numbers are on the dashboard."
)
UNGROUNDED_TEMPLATE: Final = "Here are the figures from your data for {periods}."
UNGROUNDED_NO_PERIOD: Final = "Here are the figures from your data."
INCOMPLETE_ANSWER: Final = "I could not finish this answer. Please try asking in a simpler way."
READ_ONLY_ANSWER: Final = "I can only read your data. I cannot change, delete or mark anything."
PERIOD_SEPARATOR: Final = "; "

TAX_PATTERN: Final = re.compile(
    r"\b(" + "|".join(re.escape(word) for word in TAX_KEYWORDS) + r")",
    re.IGNORECASE,
)


def is_tax_question(question: str) -> bool:
    """Word-start match so "tax" and "taxes" count, but "syntax" does not."""
    return TAX_PATTERN.search(question) is not None


def join_periods(period_labels: list[str]) -> str:
    return PERIOD_SEPARATOR.join(period_labels) if period_labels else ANY_PERIOD


def no_data_answer(period_labels: list[str]) -> str:
    return NO_DATA_TEMPLATE.format(periods=join_periods(period_labels))


def ungrounded_answer(period_labels: list[str]) -> str:
    if not period_labels:
        return UNGROUNDED_NO_PERIOD
    return UNGROUNDED_TEMPLATE.format(periods=join_periods(period_labels))
