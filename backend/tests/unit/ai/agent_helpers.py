"""Shared stubs for the agent unit tests: a stub tool runner and a scripted LLM."""

from datetime import UTC, datetime
from typing import Any, cast

from sqlalchemy.orm import Session

from app.ai.agent import RunTool, answer_question
from app.ai.llm import LlmClient, LlmRequest, LlmResponse
from app.ai.types import Figure, ToolResult
from app.schemas.chat import ChatIn, ChatOut, ChatTurn

NOW = datetime(2026, 11, 10, 6, 0, tzinfo=UTC)
PERIOD = "Last quarter (1 Jul 2026 – 30 Sep 2026)"
SESSION = cast(Session, None)


def stub_result(name: str, has_data: bool = True) -> ToolResult:
    content: dict[str, Any] = {"period": {"label": PERIOD}, "has_data": has_data}
    figures: list[Figure] = []
    if has_data:
        content.update(fx_loss_inr="38000.00", payment_count=18)
        figures = [
            Figure(label="FX loss", kind="money", value="38000.00", currency="INR", period=PERIOD)
        ]
    return ToolResult(
        name=name, content=content, has_data=has_data, figures=figures, period_label=PERIOD
    )


def stub_tool(session: Session, name: str, arguments: dict[str, Any], now: datetime) -> ToolResult:
    return stub_result(name)


def empty_tool(session: Session, name: str, arguments: dict[str, Any], now: datetime) -> ToolResult:
    return stub_result(name, has_data=False)


class ScriptedLlm:
    """Returns the given responses in order and records each request."""

    def __init__(self, *responses: LlmResponse) -> None:
        self.responses = list(responses)
        self.requests: list[LlmRequest] = []

    def create(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request.model_copy(deep=True))
        return self.responses.pop(0)


def tool_use(*names: str) -> LlmResponse:
    blocks = [
        {"type": "tool_use", "id": f"t{i}", "name": n, "input": {}} for i, n in enumerate(names)
    ]
    return LlmResponse(
        content=[{"type": "thinking", "thinking": "", "signature": "s"}, *blocks],
        stop_reason="tool_use",
    )


def text(answer: str, stop_reason: str = "end_turn") -> LlmResponse:
    return LlmResponse(content=[{"type": "text", "text": answer}], stop_reason=stop_reason)


def ask(
    llm: LlmClient,
    question: str,
    run_tool: RunTool = stub_tool,
    history: list[ChatTurn] | None = None,
) -> ChatOut:
    chat = ChatIn(question=question, history=history or [])
    return answer_question(SESSION, llm, chat, NOW, run_tool=run_tool)
