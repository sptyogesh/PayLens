"""Agent fallbacks (FR-004, FR-009): LLM errors, unfinished answers, rounds, invented numbers."""

import pytest

from app.ai.answer_rules import INCOMPLETE_ANSWER, UNAVAILABLE_ANSWER
from app.ai.llm import LlmRequest, LlmResponse
from app.ai.tools import run_tool
from app.common.constants import LLM_MAX_TOOL_ROUNDS
from app.common.errors import LlmConfigError
from app.fakes.llm_fake import FakeLlm
from tests.unit.ai.agent_helpers import PERIOD, ScriptedLlm, ask, text, tool_use


def test_llm_failure_is_a_friendly_fallback() -> None:
    out = ask(FakeLlm(), "FAKE_FAIL income")
    assert (out.outcome, out.answer, out.figures) == ("fallback", UNAVAILABLE_ANSWER, [])


def test_llm_config_error_is_a_fallback_and_keeps_figures() -> None:
    class Broken(ScriptedLlm):
        def create(self, request: LlmRequest) -> LlmResponse:
            if self.requests:
                raise LlmConfigError("bad key")
            return super().create(request)

    out = ask(Broken(tool_use("fee_summary")), "Fees?")
    assert out.outcome == "fallback"
    assert out.answer == UNAVAILABLE_ANSWER
    assert [f.value for f in out.figures] == ["38000.00"]


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens", "pause_turn"])
def test_unfinished_answers_fall_back_with_figures(stop_reason: str) -> None:
    out = ask(ScriptedLlm(tool_use("fee_summary"), text("₹38000.00", stop_reason)), "Fees?")
    assert out.outcome == "fallback"
    assert out.answer == f"Here are the figures from your data for {PERIOD}."
    assert out.figures[0].value == "38000.00"


def test_refusal_without_tools_falls_back() -> None:
    out = ask(ScriptedLlm(text("", "refusal")), "Fees?")
    assert (out.outcome, out.answer) == ("fallback", INCOMPLETE_ANSWER)


def test_round_limit_stops_the_loop() -> None:
    llm = FakeLlm()
    out = ask(llm, "FAKE_LOOP fees")
    assert len(llm.requests) == LLM_MAX_TOOL_ROUNDS + 1
    assert len(out.tools_used) == LLM_MAX_TOOL_ROUNDS
    assert out.outcome == "fallback"
    assert out.figures


def test_invented_number_falls_back_and_keeps_figures() -> None:
    out = ask(FakeLlm(), "FAKE_INVENT income last quarter")
    assert out.outcome == "fallback"
    assert "99,999.99" not in out.answer
    assert out.figures[0].value == "38000.00"


def test_numbers_without_any_tool_fall_back() -> None:
    out = ask(ScriptedLlm(text("You earned ₹5,00,000.")), "Income?")
    assert (out.outcome, out.answer) == ("fallback", INCOMPLETE_ANSWER)


def test_extreme_tool_dates_never_raise() -> None:
    """Review fix: year 1 / 9999 used to overflow in period resolution and return a 500."""
    call = LlmResponse(
        content=[
            {
                "type": "tool_use",
                "id": "t0",
                "name": "income_summary",
                "input": {"start": "0001-01-01", "end": "9999-12-31"},
            }
        ],
        stop_reason="tool_use",
    )
    llm = ScriptedLlm(call, text("I could not use those dates."))
    out = ask(llm, "Income since year 1?", run_tool=run_tool)
    assert out.outcome in {"answered", "fallback"}
    tool_message = llm.requests[1].messages[-1]["content"][0]
    assert tool_message["is_error"] is True
