"""run_tool turns resolution errors (overflow, bad values) into ToolInputError (review fix)."""

from datetime import UTC, datetime
from typing import Any, cast

import pytest
from sqlalchemy.orm import Session

from app.ai.tools import TOOLS, run_tool
from app.ai.tools.period_input import PeriodInput
from app.ai.tools.tool import Tool
from app.ai.types import ToolInputError, ToolResult

NOW = datetime(2026, 11, 10, 6, 0, tzinfo=UTC)
SESSION = cast(Session, None)


def raising(error: Exception) -> Tool:
    def run(session: Session, arguments: dict[str, Any], now: datetime) -> ToolResult:
        raise error

    return Tool(name="income_summary", description="", input_model=PeriodInput, run=run)


@pytest.mark.parametrize("error", [OverflowError("date value out of range"), ValueError("bad")])
def test_resolution_errors_become_tool_input_errors(
    monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    monkeypatch.setitem(TOOLS, "income_summary", raising(error))
    with pytest.raises(ToolInputError) as caught:
        run_tool(SESSION, "income_summary", {}, NOW)
    assert "out of range" not in str(caught.value)


def test_tool_input_errors_pass_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(TOOLS, "income_summary", raising(ToolInputError("Client not found")))
    with pytest.raises(ToolInputError, match="Client not found"):
        run_tool(SESSION, "income_summary", {}, NOW)
