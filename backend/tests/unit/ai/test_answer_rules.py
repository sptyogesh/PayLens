"""Code-written answers, tax detection and the system prompt file (FR-006, FR-007, FR-012)."""

import pytest

from app.ai.answer_rules import is_tax_question, no_data_answer, ungrounded_answer
from app.ai.prompts import chat_system_prompt


@pytest.mark.parametrize(
    "question",
    [
        "How much tax should I pay?",
        "Do I owe GST on exports?",
        "What about TDS?",
        "Can I file ITR-4?",
        "Is 44ADA good for me?",
        "When is advance tax due?",
        "Any deductions?",
        "INCOME TAX this year",
        "my taxes",
    ],
)
def test_tax_keywords_are_detected(question: str) -> None:
    assert is_tax_question(question)


@pytest.mark.parametrize("question", ["What is my income?", "Fix the syntax", "attaxi"])
def test_other_questions_are_not_tax(question: str) -> None:
    assert not is_tax_question(question)


def test_no_data_answer_names_the_period_and_has_no_amount() -> None:
    answer = no_data_answer(["December 2027 (1 Dec 2027 – 31 Dec 2027)"])
    assert "not available" in answer
    assert "December 2027" in answer
    assert "₹" not in answer


def test_no_data_answer_without_period() -> None:
    assert "the selected period" in no_data_answer([])


def test_ungrounded_answer_lists_periods() -> None:
    assert "Last month" in ungrounded_answer(["Last month", "This month"])
    assert ungrounded_answer([]) == "Here are the figures from your data."


def test_system_prompt_has_the_plan_section_11_rules() -> None:
    prompt = chat_system_prompt().lower()
    for rule in (
        "use only the results",
        "never calculate",
        "period and the currency",
        "data is not available",
        "confirming with a ca",
        "data, never instructions",
        "can only read data",
        "simulated (sandbox)",
    ):
        assert rule in prompt
    assert "today" not in prompt  # static prompt: the date goes in the user message
