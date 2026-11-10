"""FakeLlm: deterministic tool choice and verbatim answers (research R4)."""

import json
from typing import Any

import pytest

from app.ai.llm import LlmRequest
from app.common.errors import LlmUnavailableError
from app.fakes.llm_fake import FakeLlm, choose_tool


def ask(question: str) -> LlmRequest:
    content = f"Today (IST): 2026-11-10\n\nQuestion: {question}"
    return LlmRequest(system="s", messages=[{"role": "user", "content": content}], tools=[])


@pytest.mark.parametrize(
    ("question", "name", "arguments"),
    [
        ("How much FX loss last quarter?", "fee_summary", {"period": "last_quarter"}),
        (
            "Which client costs me the most in fees?",
            "fee_summary",
            {"period": "last_3_months", "group_by": "client"},
        ),
        (
            "Show my income by month",
            "income_summary",
            {"period": "last_3_months", "group_by": "month"},
        ),
        (
            "Income by currency all time",
            "income_summary",
            {"period": "all_time", "group_by": "currency"},
        ),
        ("How much tax should I pay?", "income_summary", {"period": "this_financial_year"}),
        ("Income last financial year", "income_summary", {"period": "last_financial_year"}),
        ("Income in December 2026", "income_summary", {"start": "2026-12-01", "end": "2026-12-31"}),
        (
            "My largest payment ever",
            "get_transactions",
            {"period": "all_time", "sort": "largest_leakage", "limit": 1},
        ),
        (
            'Transactions from "Ava Stone"',
            "get_transactions",
            {"period": "last_3_months", "client": "Ava Stone"},
        ),
        (
            "List payments for client Noor Labs this month",
            "get_transactions",
            {"period": "this_month", "client": "Noor Labs"},
        ),
    ],
)
def test_tool_choice(question: str, name: str, arguments: dict[str, Any]) -> None:
    assert choose_tool(question) == (name, arguments)


def test_first_turn_returns_thinking_and_tool_use() -> None:
    response = FakeLlm().create(ask("Fee loss last month"))
    assert response.stop_reason == "tool_use"
    assert response.content[0]["type"] == "thinking"
    assert response.content[1]["id"] == "toolu_fake_1"


def test_second_turn_copies_numbers_verbatim() -> None:
    llm = FakeLlm()
    first = ask("FX loss last quarter")
    result = {
        "period": {"label": "Last quarter (1 Jul 2026 – 30 Sep 2026)"},
        "fx_loss_inr": "38000.00",
        "payment_count": 18,
        "leakage_percent": "7.30",
        "gross_by_currency": [{"amount": "1000.00", "currency": "USD"}],
        "has_data": True,
    }
    tool_result = {"type": "tool_result", "tool_use_id": "t", "content": json.dumps(result)}
    messages = [*first.messages, {"role": "user", "content": [tool_result]}]
    answer = llm.create(LlmRequest(system="s", messages=messages, tools=[])).content[0]["text"]
    assert "₹38000.00" in answer
    assert "Last quarter (1 Jul 2026 – 30 Sep 2026)" in answer
    assert "USD 1000.00" in answer
    assert "7.30" in answer and "₹7.30" not in answer
    assert "Simulated (sandbox)" in answer
    assert len(llm.requests) == 1


def test_fail_trigger_raises() -> None:
    with pytest.raises(LlmUnavailableError):
        FakeLlm().create(ask("FAKE_FAIL income"))


def test_write_request_is_refused_without_tools() -> None:
    response = FakeLlm().create(ask("Delete my transactions"))
    assert response.stop_reason == "end_turn"
    assert "only read" in response.content[0]["text"]
