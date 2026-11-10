"""Ask Your Money agent loop (FR-004 to FR-009, research R1).

The LLM may call read-only tools for up to LLM_MAX_TOOL_ROUNDS rounds. Code then decides what
the user sees: figures come from tool results, never from LLM text; empty results get the
code-written "not available" answer; any number not found in a tool result replaces the answer
with a safe sentence; tax questions get the CA disclaimer. LLM failures never raise.
Child: `outcome.py` (AgentState and the final decision).
"""

import json
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.ai.llm import LlmClient, LlmRequest
from app.ai.outcome import AgentState, decide
from app.ai.prompts import chat_system_prompt
from app.ai.tools import TOOL_DEFINITIONS
from app.ai.tools import run_tool as default_run_tool
from app.ai.types import ToolInputError, ToolResult
from app.common.constants import (
    CHAT_DEADLINE_S,
    CHAT_MIN_CALL_S,
    LLM_MAX_TOOL_ROUNDS,
    LLM_TIMEOUT_S,
    LLM_TOOL_ERROR_MAX,
)
from app.common.dates import ist_date
from app.common.errors import LlmConfigError, LlmUnavailableError
from app.schemas.chat import ChatIn, ChatOut, ChatTurn

logger = logging.getLogger(__name__)

RunTool = Callable[[Session, str, dict[str, Any], datetime], ToolResult]
TOOL_USE = "tool_use"
FINAL_STOP_REASONS = frozenset({"end_turn", "stop_sequence"})
TODAY_PREFIX = "Today (IST): "
QUESTION_PREFIX = "Question: "
TOOL_ERROR_PREFIX = "Invalid tool input: "
DEADLINE_MESSAGE = "The assistant took too long."
monotonic = time.monotonic  # module-level so tests can move the clock


@dataclass(frozen=True)
class ToolRunner:
    session: Session
    now: datetime
    run: RunTool


def answer_question(
    session: Session,
    llm: LlmClient,
    chat: ChatIn,
    now: datetime,
    *,
    run_tool: RunTool = default_run_tool,
) -> ChatOut:
    """Answer a validated chat request (question + history). Never raises for LLM failures."""
    question = chat.question
    today = ist_date(now).isoformat()
    state = AgentState(messages=build_messages(question, chat.history, today))
    try:
        run_loop(state, llm, ToolRunner(session, now, run_tool))
    except LlmConfigError as error:
        logger.error("Chat LLM rejected the request (check LLM_API_KEY/LLM_MODEL): %s", error.code)
        state.llm_failed = True
    except LlmUnavailableError as error:
        logger.warning("Chat LLM unavailable: %s", error.code)
        state.llm_failed = True
    out = decide(state, question, today)
    logger.info(
        "Chat answered: outcome=%s stop=%s tools=%s",
        out.outcome,
        state.stop_reason or "-",
        out.tools_used,
    )
    return out


def build_messages(question: str, history: list[ChatTurn], today: str) -> list[dict[str, Any]]:
    """History as alternating text turns (starting with the user), then the new question."""
    messages: list[dict[str, Any]] = []
    for turn in history:
        if not turn.content.strip() or (not messages and turn.role == "assistant"):
            continue
        if messages and messages[-1]["role"] == turn.role:
            messages[-1]["content"] += "\n\n" + turn.content
        else:
            messages.append({"role": turn.role, "content": turn.content})
    content = f"{TODAY_PREFIX}{today}\n\n{QUESTION_PREFIX}{question}"
    if messages and messages[-1]["role"] == "user":
        messages[-1]["content"] += "\n\n" + content  # unanswered turn: keep roles alternating
    else:
        messages.append({"role": "user", "content": content})
    return messages


def run_loop(state: AgentState, llm: LlmClient, runner: ToolRunner) -> None:
    system = chat_system_prompt()
    deadline = monotonic() + CHAT_DEADLINE_S
    for round_number in range(LLM_MAX_TOOL_ROUNDS + 1):
        remaining = deadline - monotonic()
        if remaining < CHAT_MIN_CALL_S:
            raise LlmUnavailableError(DEADLINE_MESSAGE, code="LLM_DEADLINE")
        request = LlmRequest(
            system=system,
            messages=state.messages,
            tools=TOOL_DEFINITIONS,
            timeout_s=min(LLM_TIMEOUT_S, remaining),
        )
        response = llm.create(request)
        state.stop_reason = response.stop_reason
        state.messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != TOOL_USE:
            if response.stop_reason in FINAL_STOP_REASONS:
                state.text = response_text(response.content)
            return
        if round_number == LLM_MAX_TOOL_ROUNDS:
            return  # round limit reached: answer with the figures collected so far
        state.messages.append(
            {"role": "user", "content": run_tools(state, response.content, runner)}
        )


def response_text(content: list[dict[str, Any]]) -> str:
    texts = [block.get("text") for block in content if block.get("type") == "text"]
    return "\n".join(text for text in texts if isinstance(text, str)).strip()


def run_tools(
    state: AgentState, content: list[dict[str, Any]], runner: ToolRunner
) -> list[dict[str, Any]]:
    """Run every tool_use block; return all tool_result blocks for ONE user message."""
    blocks: list[dict[str, Any]] = []
    for block in content:
        if block.get("type") != TOOL_USE:
            continue
        name = str(block.get("name", ""))
        state.tools_used.append(name)
        result_block: dict[str, Any] = {"type": "tool_result", "tool_use_id": block.get("id")}
        try:
            arguments = block.get("input") or {}
            result = runner.run(runner.session, name, arguments, runner.now)
        except ToolInputError as error:
            logger.info("Chat tool %s rejected its input", name)
            result_block.update(content=tool_error_text(error), is_error=True)
        else:
            state.results.append(result)
            result_block["content"] = json.dumps(result.content, ensure_ascii=False)
        blocks.append(result_block)
    return blocks


def tool_error_text(error: ToolInputError) -> str:
    return (TOOL_ERROR_PREFIX + str(error))[:LLM_TOOL_ERROR_MAX]
