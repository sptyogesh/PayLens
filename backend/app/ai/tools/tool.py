"""What every chat tool is made of, and the figure builders they share (FR-003, FR-005)."""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.types import Figure, ToolResult
from app.common.constants import INR

ToolRunner = Callable[[Session, dict[str, Any], datetime], ToolResult]


@dataclass(frozen=True)
class Tool:
    """A read-only tool: its name, description for the LLM, input model and runner.

    `run` validates the raw arguments with `input_model` (raising pydantic.ValidationError).
    """

    name: str
    description: str
    input_model: type[BaseModel]
    run: ToolRunner


def money_figure(label: str, amount: str, period: str) -> Figure:
    return Figure(label=label, kind="money", value=amount, currency=INR, period=period)


def count_figure(label: str, count: int, period: str) -> Figure:
    return Figure(label=label, kind="count", value=str(count), currency=None, period=period)


def percent_figure(label: str, percent: str, period: str) -> Figure:
    return Figure(label=label, kind="percent", value=percent, currency=None, period=period)
