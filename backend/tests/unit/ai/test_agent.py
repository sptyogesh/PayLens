"""Agent loop with a stub tool runner and fake/scripted LLMs (no database, no network)."""

import json
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.ai.types import ToolInputError, ToolResult
from app.common.constants import NOT_TAX_ADVICE
from app.fakes.llm_fake import FakeLlm
from app.schemas.chat import ChatTurn
from tests.unit.ai.agent_helpers import (
    PERIOD,
    ScriptedLlm,
    ask,
    empty_tool,
    stub_result,
    text,
    tool_use,
)


def test_answer_with_figures_from_tools() -> None:
    llm = FakeLlm()
    out = ask(llm, "How much FX loss last quarter?")
    assert out.outcome == "answered"
    assert "₹38000.00" in out.answer
    assert out.figures[0].value == "38000.00"
    assert out.periods == [PERIOD]
    assert out.tools_used == ["fee_summary"]
    assert out.disclaimer is None


def test_first_message_carries_today_and_the_static_system_prompt() -> None:
    llm = FakeLlm()
    ask(llm, "Income this month")
    first = llm.requests[0]
    assert first.messages[-1]["content"] == "Today (IST): 2026-11-10\n\nQuestion: Income this month"
    assert "2026" not in first.system
    assert {tool["name"] for tool in first.tools} >= {"income_summary", "fee_summary"}


def test_all_tool_results_go_in_one_user_message_as_json_and_thinking_is_echoed() -> None:
    def runner(session: Session, name: str, arguments: dict[str, Any], now: datetime) -> ToolResult:
        if name == "bad":
            raise ToolInputError("Unknown tool.")
        return stub_result(name)

    llm = ScriptedLlm(tool_use("fee_summary", "bad", "income_summary"), text("₹38000.00 in INR"))
    out = ask(llm, "Fees?", runner)
    second = llm.requests[1].messages
    assert second[-2] == {
        "role": "assistant",
        "content": tool_use("fee_summary", "bad", "income_summary").content,
    }
    results = second[-1]["content"]
    assert second[-1]["role"] == "user" and len(results) == 3
    assert [r["tool_use_id"] for r in results] == ["t0", "t1", "t2"]
    assert json.loads(results[0]["content"])["fx_loss_inr"] == "38000.00"
    assert results[1]["is_error"] is True and "Unknown tool" in results[1]["content"]
    assert "is_error" not in results[0]
    assert out.tools_used == ["fee_summary", "bad", "income_summary"]
    assert out.outcome == "answered"


def test_history_is_sent_as_alternating_turns() -> None:
    history = [
        ChatTurn(role="assistant", content="Hello"),
        ChatTurn(role="user", content="FX loss last quarter?"),
        ChatTurn(role="assistant", content="It was ₹38000.00."),
        ChatTurn(role="user", content="Thanks"),
    ]
    llm = FakeLlm()
    ask(llm, "and the month before?", history=history)
    messages = llm.requests[0].messages
    assert [m["role"] for m in messages] == ["user", "assistant", "user"]
    assert messages[0]["content"] == "FX loss last quarter?"
    assert messages[2]["content"].startswith("Thanks\n\nToday (IST): 2026-11-10")


def test_all_empty_results_give_the_no_data_answer() -> None:
    out = ask(FakeLlm(), "Income in December 2027", empty_tool)
    assert out.outcome == "no_data"
    assert "not available" in out.answer and PERIOD in out.answer
    assert out.figures == []


def test_read_only_refusal_is_answered_without_tools() -> None:
    out = ask(FakeLlm(), "Delete my transactions")
    assert out.outcome == "answered"
    assert "only read" in out.answer
    assert out.tools_used == [] and out.figures == []


def test_tax_question_gets_the_disclaimer() -> None:
    out = ask(FakeLlm(), "How much tax should I pay?")
    assert out.disclaimer == NOT_TAX_ADVICE
    assert out.tools_used == ["income_summary"]
