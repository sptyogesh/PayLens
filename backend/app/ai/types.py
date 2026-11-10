"""Types shared by the chat tools and the agent (contracts/http-api.md, internal interfaces)."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class Figure(BaseModel):
    """One number shown under an answer. Always copied from a tool result by code (FR-005)."""

    model_config = ConfigDict(frozen=True)

    label: str
    kind: Literal["money", "count", "percent"]
    value: str
    currency: str | None
    period: str


class ToolResult(BaseModel):
    """What a read-only tool returns: JSON-safe content for the LLM plus what code needs."""

    model_config = ConfigDict(frozen=True)

    name: str
    content: dict[str, Any]
    has_data: bool
    figures: list[Figure]
    period_label: str


class ToolInputError(ValueError):
    """Unknown tool or arguments that fail validation; sent back to the LLM as an error result."""
