"""Chat, FIRA extraction and report summary through GeminiLlm (respx-mocked, fake key).

The same grounding and number checks apply as with Anthropic: the agent, extractor and summary
code are unchanged; only the adapter differs.
"""

import base64
import json
from typing import Any

import httpx
import pytest
import respx

from app.ai.answer_rules import BUSY_ANSWER, UNAVAILABLE_ANSWER
from app.ai.fira_extract import EXTRACTION_SCHEMA, extract
from app.ai.gemini import GeminiLlm
from app.ai.report_summary import write_summary
from app.ai.tools import run_tool
from app.common.constants import FIRA_PDF_MEDIA_TYPE, GEMINI_JSON_MIME
from tests.fixtures.fira import VALID_FIELDS, fira_pdf
from tests.fixtures.report import figures
from tests.unit.ai.agent_helpers import PERIOD, ask
from tests.unit.ai.gemini_helpers import BASE, KEY, MODEL, URL, call_part, reply


@pytest.fixture
def llm() -> GeminiLlm:
    return GeminiLlm(httpx.Client(base_url=BASE), KEY, MODEL)


def bodies(route: respx.Route) -> list[dict[str, Any]]:
    return [json.loads(call.request.content) for call in route.calls]


@respx.mock
def test_multi_step_chat_echoes_ids_names_and_signatures(llm: GeminiLlm) -> None:
    route = respx.post(URL).mock(
        side_effect=[
            httpx.Response(200, json=reply([call_part("fee_summary", "c1", "sig-A")])),
            httpx.Response(200, json=reply([call_part("income_summary", "c2", "sig-B")])),
            httpx.Response(200, json=reply([{"text": "FX loss was ₹38000.00 in INR."}])),
        ]
    )
    out = ask(llm, "How much FX loss last quarter?")
    assert (out.outcome, out.answer) == ("answered", "FX loss was ₹38000.00 in INR.")
    assert out.tools_used == ["fee_summary", "income_summary"]
    third = bodies(route)[2]["contents"]
    assert [turn["role"] for turn in third] == ["user", "model", "user", "model", "user"]
    assert third[1]["parts"][0]["thoughtSignature"] == "sig-A"
    assert third[3]["parts"][0]["thoughtSignature"] == "sig-B"
    response = third[2]["parts"][0]["functionResponse"]
    assert (response["id"], response["name"]) == ("c1", "fee_summary")
    assert response["response"]["fx_loss_inr"] == "38000.00"


@respx.mock
def test_invented_number_from_gemini_is_replaced_by_code(llm: GeminiLlm) -> None:
    respx.post(URL).mock(
        side_effect=[
            httpx.Response(200, json=reply([call_part("fee_summary", "c1", "s")])),
            httpx.Response(200, json=reply([{"text": "FX loss was ₹99,999.00."}])),
        ]
    )
    out = ask(llm, "FX loss?")
    assert out.outcome == "fallback"
    assert out.answer == f"Here are the figures from your data for {PERIOD}."
    assert [f.value for f in out.figures] == ["38000.00"]  # figures still come from the tool


@respx.mock
def test_tool_input_error_is_sent_back_as_an_error_response(llm: GeminiLlm) -> None:
    route = respx.post(URL).mock(
        side_effect=[
            httpx.Response(200, json=reply([call_part("no_such_tool", "c1", "s")])),
            httpx.Response(200, json=reply([{"text": "I cannot answer that."}])),
        ]
    )
    ask(llm, "Something?", run_tool)
    response = bodies(route)[1]["contents"][2]["parts"][0]["functionResponse"]
    assert response["id"] == "c1" and "Unknown tool" in response["response"]["error"]


@respx.mock
def test_quota_429_gives_the_busy_answer(llm: GeminiLlm) -> None:
    respx.post(URL).respond(429, json={"error": {"code": 429, "status": "RESOURCE_EXHAUSTED"}})
    out = ask(llm, "Income this month?")
    assert (out.outcome, out.answer) == ("fallback", BUSY_ANSWER)
    assert "busy" in out.answer and "try again shortly" in out.answer


@respx.mock
def test_server_error_keeps_the_unavailable_answer(llm: GeminiLlm) -> None:
    respx.post(URL).respond(503, json={"error": {"code": 503}})
    assert ask(llm, "Income this month?").answer == UNAVAILABLE_ANSWER


@respx.mock
def test_fira_pdf_is_sent_inline_with_the_strict_schema(llm: GeminiLlm) -> None:
    route = respx.post(URL).respond(200, json=reply([{"text": json.dumps(VALID_FIELDS)}]))
    pdf = fira_pdf()
    outcome = extract(llm, pdf, "fira.pdf")
    assert outcome.problems == [] and str(outcome.extraction.foreign_amount) == "1000.00"
    body = bodies(route)[0]
    inline = body["contents"][0]["parts"][0]["inlineData"]
    assert inline == {"mimeType": FIRA_PDF_MEDIA_TYPE, "data": base64.b64encode(pdf).decode()}
    response_format = body["generationConfig"]["responseFormat"]["text"]
    assert response_format == {"mimeType": GEMINI_JSON_MIME, "schema": EXTRACTION_SCHEMA}


@respx.mock
def test_fira_json_split_over_parts_with_a_signature_part_is_read(llm: GeminiLlm) -> None:
    raw = json.dumps(VALID_FIELDS)
    parts = [{"text": "", "thoughtSignature": "s"}, {"text": raw[:20]}, {"text": raw[20:]}]
    respx.post(URL).respond(200, json=reply(parts))
    assert extract(llm, fira_pdf(), "fira.pdf").problems == []


@respx.mock
def test_fira_values_from_gemini_are_still_checked_by_code(llm: GeminiLlm) -> None:
    wrong = {**VALID_FIELDS, "inr_amount": "90000.00"}
    respx.post(URL).respond(200, json=reply([{"text": json.dumps(wrong)}]))
    assert any("INR amount" in p for p in extract(llm, fira_pdf(), "fira.pdf").problems)


@respx.mock
def test_report_summary_from_gemini_is_grounded_or_replaced(llm: GeminiLlm) -> None:
    respx.post(URL).respond(200, json=reply([{"text": "Income was ₹1,68,000.00 this month."}]))
    assert write_summary(llm, figures()).source == "ai"
    respx.post(URL).respond(200, json=reply([{"text": "Income was ₹2,00,000.00 this month."}]))
    assert write_summary(llm, figures()).source == "code"
