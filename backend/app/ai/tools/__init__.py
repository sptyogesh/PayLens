"""Read-only chat tools (FR-003). Public entry: TOOL_DEFINITIONS and run_tool.

Children: `period_input` (shared period argument), `tool` (Tool spec, figure builders),
`income_summary`, `fee_summary`, `get_transactions`, `fira_status`. No tool writes or commits
anything.
"""

from datetime import datetime
from typing import Any, Final

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.ai.tools import fee_summary, fira_status, get_transactions, income_summary
from app.ai.tools.tool import Tool
from app.ai.types import ToolInputError, ToolResult
from app.common.dates import ensure_utc

TOOLS: Final[dict[str, Tool]] = {
    tool.name: tool
    for tool in (income_summary.TOOL, fee_summary.TOOL, get_transactions.TOOL, fira_status.TOOL)
}
MAX_ERRORS_SHOWN: Final = 3
UNRESOLVABLE_MESSAGE: Final = "the period could not be resolved"


def tool_definition(tool: Tool) -> dict[str, Any]:
    """Anthropic tool JSON. The schema comes from the Pydantic input model (extra="forbid")."""
    schema = tool.input_model.model_json_schema()
    schema["additionalProperties"] = False
    return {"name": tool.name, "description": tool.description, "input_schema": schema}


TOOL_DEFINITIONS: Final[list[dict[str, Any]]] = [tool_definition(t) for t in TOOLS.values()]


def safe_message(name: str, error: ValidationError) -> str:
    """Field paths and messages only; the rejected input values are never echoed back."""
    parts = [
        f"{'.'.join(str(p) for p in e['loc']) or 'arguments'}: {e['msg']}"
        for e in error.errors()[:MAX_ERRORS_SHOWN]
    ]
    return f"Invalid arguments for {name}: " + "; ".join(parts)


def run_tool(session: Session, name: str, arguments: dict[str, Any], now: datetime) -> ToolResult:
    tool = TOOLS.get(name)
    if tool is None:
        raise ToolInputError("Unknown tool. Available tools: " + ", ".join(TOOLS))
    try:
        return tool.run(session, arguments, ensure_utc(now))
    except ValidationError as error:
        raise ToolInputError(safe_message(name, error)) from error
    except ToolInputError:
        raise
    except (OverflowError, ValueError) as error:  # e.g. a period that cannot be resolved
        raise ToolInputError(f"Invalid arguments for {name}: {UNRESOLVABLE_MESSAGE}") from error


__all__ = ["TOOL_DEFINITIONS", "run_tool"]
