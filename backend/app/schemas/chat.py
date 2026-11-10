"""POST /chat request and response (contracts/http-api.md, FR-001)."""

from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.ai.types import Figure
from app.common.constants import CHAT_HISTORY_ITEM_MAX, CHAT_HISTORY_MAX, CHAT_QUESTION_MAX

ChatOutcome = Literal["answered", "no_data", "fallback"]
Question = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=CHAT_QUESTION_MAX)
]
TurnText = Annotated[str, StringConstraints(max_length=CHAT_HISTORY_ITEM_MAX)]


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: TurnText


class ChatIn(BaseModel):
    question: Question
    history: list[ChatTurn] = Field(default_factory=list, max_length=CHAT_HISTORY_MAX)


class FigureOut(BaseModel):
    """A figure behind the answer, copied from a tool result by code (FR-005)."""

    label: str
    kind: Literal["money", "count", "percent"]
    value: str
    currency: str | None
    period: str

    @classmethod
    def of(cls, figure: Figure) -> "FigureOut":
        return cls.model_validate(figure.model_dump())


class ChatOut(BaseModel):
    answer: str
    outcome: ChatOutcome
    periods: list[str]
    figures: list[FigureOut]
    disclaimer: str | None
    tools_used: list[str]
