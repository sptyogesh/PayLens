"""Deterministic fake LLM for tests and E2E (LLM_MODE=fake, APP_ENV=test only; research R4).

Turn 1 picks a tool from keywords in the question. Turn 2 writes an answer that copies the
numbers from the tool results verbatim. Trigger words force the failure paths tests need.
"""

import calendar
import json
import re
from typing import Any, Final

from app.ai.answer_rules import READ_ONLY_ANSWER
from app.ai.llm import LlmRequest, LlmResponse
from app.common.constants import SIMULATED_LABEL
from app.common.errors import LlmUnavailableError
from app.fakes.llm_fake_fira import describe_fira, extraction_text
from app.fakes.llm_fake_report import ReportMode, report_data, report_summary_text

FAKE_FAIL: Final = "FAKE_FAIL"
FAKE_INVENT: Final = "FAKE_INVENT"
FAKE_LOOP: Final = "FAKE_LOOP"
FAKE_WRITE: Final = "FAKE_WRITE"
INVENTED_AMOUNT: Final = "₹99,999.99"
QUESTION_MARKER: Final = "Question: "
THINKING_BLOCK: Final = {"type": "thinking", "thinking": "", "signature": "fake"}
WRITE_WORDS: Final = re.compile(r"\b(delete|mark|remove|update|change)\b", re.IGNORECASE)
TOOL_KEYWORDS: Final = (
    ("fira_status", re.compile(r"\bfira", re.IGNORECASE)),
    ("fee_summary", re.compile(r"\b(fee|fx|leakage|loss|cost)", re.IGNORECASE)),
    ("income_summary", re.compile(r"\b(income|earn|revenue|paid|tax)", re.IGNORECASE)),
    ("get_transactions", re.compile(r"\b(transaction|payment|list|show|largest)", re.IGNORECASE)),
)
GROUP_WORDS: Final = (("client", "client"), ("month", "month"), ("currency", "currency"))
PERIOD_WORDS: Final = (
    ("last financial year", "last_financial_year"),
    ("last quarter", "last_quarter"),
    ("this quarter", "this_quarter"),
    ("last 3 months", "last_3_months"),
    ("last month", "last_month"),
    ("this month", "this_month"),
    ("financial year", "this_financial_year"),
    ("fy", "this_financial_year"),
    ("tax", "this_financial_year"),
    ("all time", "all_time"),
    ("ever", "all_time"),
    ("total", "all_time"),
)
DEFAULT_PERIOD: Final = "last_3_months"
MONTH_NAMES: Final = "|".join(calendar.month_name[1:])
MONTH_YEAR: Final = re.compile(rf"\b({MONTH_NAMES})\s+(\d{{4}})\b", re.IGNORECASE)
QUOTED: Final = re.compile(r"[\"']([^\"']+)[\"']")
AFTER_FOR: Final = re.compile(r"\b(?:from|for)\s+(?:client\s+)?([A-Z][\w.]*(?:\s+[A-Z][\w.]*)*)")
NUMERIC: Final = re.compile(r"^-?\d+(?:\.\d+)?$")
MONEY_HINTS: Final = ("percent", "pct", "rate", "count", "payments")


class FakeLlm:
    def __init__(self, report_mode: ReportMode = "ok") -> None:
        self.requests: list[LlmRequest] = []
        self._next_id = 0
        self.report_mode = report_mode

    def create(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        if request.output_schema is not None:
            return text_response(extraction_text(request))
        report = report_data(request)
        if report is not None:
            return text_response(report_summary_text(report, self.report_mode))
        question = latest_question(request.messages)
        if FAKE_FAIL in question:
            raise LlmUnavailableError("Fake LLM is down.")
        if FAKE_WRITE in question or WRITE_WORDS.search(question):
            return text_response(READ_ONLY_ANSWER)
        results = latest_tool_results(request.messages)
        if FAKE_LOOP in question or results is None:
            return self._tool_call(question)
        if FAKE_INVENT in question:
            return text_response(f"Your income was {INVENTED_AMOUNT} in INR.")
        return text_response(write_answer(results))

    def _tool_call(self, question: str) -> LlmResponse:
        self._next_id += 1
        name, arguments = choose_tool(question)
        block: dict[str, Any] = {"type": "tool_use", "id": f"toolu_fake_{self._next_id}"}
        block.update(name=name, input=arguments)
        return LlmResponse(content=[dict(THINKING_BLOCK), block], stop_reason="tool_use")


def text_response(text: str) -> LlmResponse:
    return LlmResponse(content=[{"type": "text", "text": text}], stop_reason="end_turn")


def latest_question(messages: list[dict[str, Any]]) -> str:
    """The text of the newest user message that is a question (not a tool-result message)."""
    for message in reversed(messages):
        content = message["content"]
        if message["role"] == "user" and isinstance(content, str):
            return content.split(QUESTION_MARKER, 1)[-1]
    return ""


def latest_tool_results(messages: list[dict[str, Any]]) -> list[dict[str, Any]] | None:
    last = messages[-1]
    if last["role"] != "user" or isinstance(last["content"], str):
        return None
    blocks = [b for b in last["content"] if b.get("type") == "tool_result"]
    return [json.loads(b["content"]) for b in blocks if not b.get("is_error")] if blocks else None


def choose_tool(question: str) -> tuple[str, dict[str, Any]]:
    name = next((n for n, pattern in TOOL_KEYWORDS if pattern.search(question)), "income_summary")
    arguments = choose_period(question)
    lowered = question.lower()
    if name == "get_transactions":
        client = find_client(question)
        if client:
            arguments["client"] = client
        if "largest" in lowered:
            arguments.update(sort="largest_leakage", limit=1)
        return name, arguments
    if name == "fira_status":
        defaulted = arguments == {"period": DEFAULT_PERIOD} and "3 months" not in lowered
        return name, {} if defaulted else arguments  # the tool defaults to all time
    group = next((g for word, g in GROUP_WORDS if word in lowered), None)
    if group and not (group == "currency" and name == "fee_summary"):
        arguments["group_by"] = group
    return name, arguments


def choose_period(question: str) -> dict[str, Any]:
    month = MONTH_YEAR.search(question)
    if month:
        number = list(calendar.month_name).index(month.group(1).capitalize())
        year = int(month.group(2))
        last_day = calendar.monthrange(year, number)[1]
        return {"start": f"{year}-{number:02d}-01", "end": f"{year}-{number:02d}-{last_day:02d}"}
    lowered = question.lower()
    for words, period in PERIOD_WORDS:
        if re.search(rf"\b{words}\b", lowered):
            return {"period": period}
    return {"period": DEFAULT_PERIOD}


def find_client(question: str) -> str | None:
    match = QUOTED.search(question) or AFTER_FOR.search(question)
    if match is None or MONTH_YEAR.match(match.group(1)):
        return None
    return match.group(1)


def write_answer(results: list[dict[str, Any]]) -> str:
    if not results:
        return "The data is not available."
    parts = [describe_result(result) for result in results]
    return " ".join(parts)


def period_label(result: dict[str, Any]) -> str:
    period = result.get("period")
    return str(period.get("label")) if isinstance(period, dict) else "the selected period"


def describe_result(result: dict[str, Any]) -> str:
    period = period_label(result)
    if not result.get("has_data", False):
        return f"The data is not available for {period}."
    if result.get("missing") is not None:
        return describe_fira(result, period)
    values = ", ".join(f"{key} {value}" for key, value in numeric_leaves(result, ""))
    note = f" FX loss uses the {SIMULATED_LABEL} rate." if "fx" in values else ""
    return f"For {period}, in INR: {values}.{note}"


def numeric_leaves(value: Any, path: str) -> list[tuple[str, str]]:
    """Every number in the result as (path, text), INR money prefixed with ₹, copied verbatim."""
    if isinstance(value, dict):
        if {"amount", "currency"} <= value.keys():
            return [(path, f"{value['currency']} {value['amount']}")]
        name = value.get("label") if "key" in value else value.get("client")
        named = [("for", str(name))] if isinstance(name, str) else []
        return named + [leaf for k, v in value.items() for leaf in numeric_leaves(v, k)]
    if isinstance(value, list):
        return [leaf for item in value for leaf in numeric_leaves(item, path)]
    if isinstance(value, bool) or value is None:
        return []
    text = str(value)
    if not NUMERIC.match(text):
        return []
    is_money = "." in text and not any(hint in path for hint in MONEY_HINTS)
    return [(path, f"₹{text}" if is_money else text)]
