"""Child of agent.py: what the user sees once the loop has finished (FR-004 to FR-007)."""

import logging
from dataclasses import dataclass, field
from typing import Any

from app.ai.answer_rules import (
    INCOMPLETE_ANSWER,
    UNAVAILABLE_ANSWER,
    is_tax_question,
    no_data_answer,
    ungrounded_answer,
)
from app.ai.grounding import allowed_numbers, number_tokens, ungrounded_numbers
from app.ai.types import ToolResult
from app.common.constants import NOT_TAX_ADVICE
from app.schemas.chat import ChatOut, ChatOutcome, FigureOut

logger = logging.getLogger(__name__)


@dataclass
class AgentState:
    """Everything the loop collected. `text` is set only when the LLM finished normally."""

    messages: list[dict[str, Any]]
    results: list[ToolResult] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    text: str = ""
    llm_failed: bool = False
    stop_reason: str = ""


def unique_periods(results: list[ToolResult]) -> list[str]:
    return list(dict.fromkeys(result.period_label for result in results))


def decide(state: AgentState, question: str, today: str) -> ChatOut:
    periods = unique_periods(state.results)
    figures = [FigureOut.of(f) for r in state.results if r.has_data for f in r.figures]
    outcome, answer = choose_answer(state, question, today, periods)
    return ChatOut(
        answer=answer,
        outcome=outcome,
        periods=periods,
        figures=[] if outcome == "no_data" else figures,
        disclaimer=NOT_TAX_ADVICE if is_tax_question(question) else None,
        tools_used=state.tools_used,
    )


def choose_answer(
    state: AgentState, question: str, today: str, periods: list[str]
) -> tuple[ChatOutcome, str]:
    if state.results and not any(result.has_data for result in state.results):
        return "no_data", no_data_answer(periods)
    if state.llm_failed:
        return "fallback", UNAVAILABLE_ANSWER
    if not state.text:
        return "fallback", ungrounded_answer(periods) if state.results else INCOMPLETE_ANSWER
    if not state.results:
        has_numbers = bool(number_tokens(state.text))
        return ("fallback", INCOMPLETE_ANSWER) if has_numbers else ("answered", state.text)
    allowed = allowed_numbers(state.results, question, [*periods, today])
    rejected = ungrounded_numbers(state.text, allowed)
    if rejected:
        logger.warning("Chat answer replaced: %d number(s) not in tool results", len(rejected))
        return "fallback", ungrounded_answer(periods)
    return "answered", state.text
