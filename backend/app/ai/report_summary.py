"""AI summary for the CA report (005 FR-003): one LLM call, no tools, grounded or replaced.

The LLM sees only the report figures as JSON. Its reply is used only when it ends normally,
is not empty and every number in it is in the figures (003 grounding rules); otherwise the
summary written by code is used. AI problems never fail the report.
"""

import logging
from typing import Final

from app.ai.grounding import allowed_from_content, ungrounded_numbers
from app.ai.llm import LlmClient, LlmRequest, LlmResponse
from app.ai.prompts import load_prompt
from app.ai.report_fallback import code_summary
from app.common.constants import LLM_TIMEOUT_S, REPORT_DATA_MARKER, REPORT_SUMMARY_MAX_CHARS
from app.common.errors import LlmConfigError, LlmUnavailableError
from app.schemas.report import ReportFigures, ReportSummary

logger = logging.getLogger(__name__)

PROMPT_FILE: Final = "report_summary.md"
END_TURN: Final = "end_turn"


def summary_request(figures: ReportFigures) -> LlmRequest:
    content = REPORT_DATA_MARKER + figures.model_dump_json()
    return LlmRequest(
        system=load_prompt(PROMPT_FILE),
        messages=[{"role": "user", "content": content}],
        timeout_s=LLM_TIMEOUT_S,
    )


def reply_text(response: LlmResponse) -> str:
    """The text of a normal reply; "" for a refusal, max_tokens or no text."""
    if response.stop_reason != END_TURN:
        return ""
    blocks = [block for block in response.content if block.get("type") == "text"]
    texts = [str(block.get("text", "")) for block in blocks]
    return " ".join(texts).strip()


def is_grounded(text: str, figures: ReportFigures) -> bool:
    content = figures.model_dump(mode="json")
    allowed = allowed_from_content(content, [figures.period.label])
    return not ungrounded_numbers(text, allowed)


def write_summary(llm: LlmClient, figures: ReportFigures) -> ReportSummary:
    try:
        text = reply_text(llm.create(summary_request(figures)))
    except (LlmUnavailableError, LlmConfigError) as error:
        logger.warning("Report summary fell back to code: %s", error.code)
        return code_summary(figures)
    if not text or len(text) > REPORT_SUMMARY_MAX_CHARS or not is_grounded(text, figures):
        logger.info("Report summary fell back to code: empty, too long or not grounded")
        return code_summary(figures)
    return ReportSummary(text=text, source="ai")
