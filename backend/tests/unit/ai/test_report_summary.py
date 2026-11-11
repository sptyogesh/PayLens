"""CA report summary (005 US2): grounded AI text, or the code summary on any problem."""

import json

import pytest

from app.ai.llm import LlmRequest, LlmResponse
from app.ai.report_fallback import code_summary
from app.ai.report_summary import write_summary
from app.common.constants import (
    LLM_TIMEOUT_S,
    REPORT_DATA_MARKER,
    REPORT_NO_PAYMENTS,
)
from app.common.errors import LlmConfigError
from app.fakes.llm_fake import FakeLlm
from app.fakes.llm_fake_report import ReportMode
from tests.fixtures.report import figures, row

CODE_TEXT = (
    "This month: 2 payments, income ₹1,68,000.00 (mid-market). Total leakage was"
    " ₹12,432.00 (7.40% of income), with FX loss at a Simulated (sandbox) rate."
    " 1 payment is missing a FIRA."
)


class StubLlm:
    def __init__(self, text: str = "", stop_reason: str = "end_turn") -> None:
        self.text, self.stop_reason = text, stop_reason

    def create(self, request: LlmRequest) -> LlmResponse:
        if self.stop_reason == "error":
            raise LlmConfigError("bad key")
        content = [{"type": "text", "text": self.text}] if self.text else []
        return LlmResponse(content=content, stop_reason=self.stop_reason)


def test_grounded_ai_summary_is_used() -> None:
    llm = FakeLlm()
    out = write_summary(llm, figures())
    assert out.source == "ai"
    assert "₹168000.00" in out.text and "This month" in out.text
    request = llm.requests[0]
    assert request.tools == [] and request.timeout_s == LLM_TIMEOUT_S
    assert "Copy every number exactly" in request.system
    sent = json.loads(request.messages[0]["content"].removeprefix(REPORT_DATA_MARKER))
    assert "summary" not in sent and sent["totals"]["payment_count"] == 2


@pytest.mark.parametrize("mode", ["fail", "invent"])
def test_failure_or_invented_number_uses_code_summary(mode: ReportMode) -> None:
    out = write_summary(FakeLlm(report_mode=mode), figures())
    assert out.source == "code" and out.text == CODE_TEXT


@pytest.mark.parametrize(
    "llm",
    [
        StubLlm(""),
        StubLlm("Income was ₹168000.00.", stop_reason="refusal"),
        StubLlm("Income was ₹168000.00.", stop_reason="max_tokens"),
        StubLlm(stop_reason="error"),
        StubLlm("Income was ₹1,68,000.01 for This month."),
        StubLlm("Leakage was 7.4% and fees 9%."),
        StubLlm("x" * 1300),
    ],
)
def test_bad_replies_use_code_summary(llm: StubLlm) -> None:
    assert write_summary(llm, figures()).source == "code"


def test_numbers_from_client_names_are_not_grounded() -> None:
    data = figures(by_client=[row("c1", "Acme 777777")])
    assert write_summary(StubLlm("You earned ₹777777 in INR."), data).source == "code"


def test_en_in_commas_are_grounded() -> None:
    text = "For This month, income was ₹1,68,000.00 in INR and 1 payments miss a FIRA."
    assert write_summary(StubLlm(text), figures()).source == "ai"


def test_code_summary_for_an_empty_period() -> None:
    out = code_summary(figures(totals=None))
    assert (out.text, out.source) == (REPORT_NO_PAYMENTS, "code")
    ai = write_summary(FakeLlm(), figures(totals=None))
    assert ai.text == "There are no payments in This month."
