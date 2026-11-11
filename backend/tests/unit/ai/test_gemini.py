"""GeminiLlm against respx-mocked generateContent (never the real service; fake key only)."""

import json
import logging
from typing import Any

import httpx
import pytest
import respx

from app.ai.gemini import GeminiLlm
from app.ai.gemini_format import SIGNATURE_KEY
from app.ai.llm import LlmRequest
from app.common.constants import GEMINI_THINKING_LEVEL, LLM_BUSY_CODE, LLM_MAX_TOKENS
from app.common.errors import LlmConfigError, LlmUnavailableError
from tests.unit.ai.gemini_helpers import BASE, KEY, MODEL, URL, call_part, reply

TOOLS = [
    {
        "name": "income_summary",
        "description": "Income for a period",
        "input_schema": {
            "$defs": {"Period": {"enum": ["this_month", "all_time"], "type": "string"}},
            "type": "object",
            "properties": {"period": {"anyOf": [{"$ref": "#/$defs/Period"}, {"type": "null"}]}},
            "additionalProperties": False,
        },
    }
]
REQUEST = LlmRequest(system="rules", messages=[{"role": "user", "content": "hi"}], tools=TOOLS)


@pytest.fixture
def llm() -> GeminiLlm:
    return GeminiLlm(httpx.Client(base_url=BASE), KEY, MODEL)


def sent_body(route: respx.Route) -> dict[str, Any]:
    body: dict[str, Any] = json.loads(route.calls.last.request.content)
    return body


@respx.mock
def test_request_uses_the_documented_url_header_and_body(llm: GeminiLlm) -> None:
    route = respx.post(URL).respond(200, json=reply([{"text": "ok"}]))
    llm.create(REQUEST)
    sent = route.calls.last.request
    assert sent.headers["x-goog-api-key"] == KEY
    assert "key=" not in str(sent.url)  # the key never goes in the URL (URLs get logged)
    body = sent_body(route)
    assert body["systemInstruction"] == {"parts": [{"text": "rules"}]}
    assert body["contents"] == [{"role": "user", "parts": [{"text": "hi"}]}]
    assert body["generationConfig"] == {
        "maxOutputTokens": LLM_MAX_TOKENS,
        "thinkingConfig": {"thinkingLevel": GEMINI_THINKING_LEVEL},
    }
    for rejected in ("temperature", "topP", "topK", "toolConfig"):
        assert rejected not in body and rejected not in body["generationConfig"]


@respx.mock
def test_tools_are_function_declarations_with_inlined_json_schema(llm: GeminiLlm) -> None:
    route = respx.post(URL).respond(200, json=reply([{"text": "ok"}]))
    llm.create(REQUEST)
    [declaration] = sent_body(route)["tools"][0]["functionDeclarations"]
    assert declaration["name"] == "income_summary"
    assert declaration["description"] == "Income for a period"
    schema = declaration["parametersJsonSchema"]
    assert "$defs" not in json.dumps(schema) and "$ref" not in json.dumps(schema)
    assert schema["properties"]["period"]["anyOf"][0]["enum"] == ["this_month", "all_time"]
    assert schema["additionalProperties"] is False


@respx.mock
def test_function_call_becomes_tool_use_with_id_and_signature(llm: GeminiLlm) -> None:
    respx.post(URL).respond(200, json=reply([call_part("fee_summary", "c1", "sig-1")]))
    response = llm.create(REQUEST)
    assert response.stop_reason == "tool_use"
    assert response.content == [
        {
            "type": "tool_use",
            "id": "c1",
            "name": "fee_summary",
            "input": {"period": "all_time"},
            SIGNATURE_KEY: "sig-1",
        }
    ]


@respx.mock
def test_parallel_calls_keep_order_and_only_the_first_signature(llm: GeminiLlm) -> None:
    parts = [call_part("fee_summary", "c1", "sig-1"), call_part("income_summary", "c2", None)]
    respx.post(URL).respond(200, json=reply(parts))
    content = llm.create(REQUEST).content
    assert [(b["id"], b.get(SIGNATURE_KEY)) for b in content] == [("c1", "sig-1"), ("c2", None)]


@respx.mock
def test_call_without_id_gets_a_local_id_that_is_never_sent_back(llm: GeminiLlm) -> None:
    route = respx.post(URL).respond(200, json=reply([call_part("fee_summary", None, "s")]))
    first = llm.create(REQUEST)
    result = {"type": "tool_result", "tool_use_id": first.content[0]["id"], "content": "{}"}
    messages = [
        *REQUEST.messages,
        {"role": "assistant", "content": first.content},
        {"role": "user", "content": [result]},
    ]
    llm.create(REQUEST.model_copy(update={"messages": messages}))
    contents = sent_body(route)["contents"]
    assert "id" not in contents[1]["parts"][0]["functionCall"]
    assert "id" not in contents[2]["parts"][0]["functionResponse"]


@respx.mock
def test_text_reply_ends_the_turn_and_thought_parts_are_dropped(llm: GeminiLlm) -> None:
    parts: list[dict[str, Any]] = [
        {"text": "thinking...", "thought": True},
        {"text": "Answer", "thoughtSignature": "s"},
    ]
    respx.post(URL).respond(200, json=reply(parts))
    response = llm.create(REQUEST)
    assert response.stop_reason == "end_turn"
    assert response.content == [{"type": "text", "text": "Answer", SIGNATURE_KEY: "s"}]


@respx.mock
@pytest.mark.parametrize(
    ("finish", "stop"),
    [
        ("MAX_TOKENS", "max_tokens"),
        ("SAFETY", "refusal"),
        ("MALFORMED_FUNCTION_CALL", "refusal"),
        (None, "refusal"),
    ],
)
def test_other_finish_reasons_are_not_final_answers(
    llm: GeminiLlm, finish: str | None, stop: str
) -> None:
    respx.post(URL).respond(200, json=reply([{"text": "partial"}], finish))
    assert llm.create(REQUEST).stop_reason == stop


@respx.mock
def test_blocked_prompt_is_a_refusal_without_content(llm: GeminiLlm) -> None:
    respx.post(URL).respond(200, json={"promptFeedback": {"blockReason": "SAFETY"}})
    response = llm.create(REQUEST)
    assert (response.content, response.stop_reason) == ([], "refusal")


@respx.mock
def test_429_quota_is_busy(llm: GeminiLlm) -> None:
    error = {"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "quota"}}
    respx.post(URL).respond(429, json=error)
    with pytest.raises(LlmUnavailableError) as caught:
        llm.create(REQUEST)
    assert caught.value.code == LLM_BUSY_CODE
    assert "busy" in caught.value.message


@respx.mock
@pytest.mark.parametrize("status", [500, 503, 504])
def test_server_errors_are_unavailable_not_busy(llm: GeminiLlm, status: int) -> None:
    respx.post(URL).respond(status, json={"error": {"code": status}})
    with pytest.raises(LlmUnavailableError) as caught:
        llm.create(REQUEST)
    assert caught.value.code != LLM_BUSY_CODE


@respx.mock
@pytest.mark.parametrize("status", [400, 402, 403, 404])
def test_rejected_requests_are_config_errors(llm: GeminiLlm, status: int) -> None:
    respx.post(URL).respond(status, json={"error": {"code": status, "status": "INVALID_ARGUMENT"}})
    with pytest.raises(LlmConfigError):
        llm.create(REQUEST)


@respx.mock
@pytest.mark.parametrize("error", [httpx.ReadTimeout("slow"), httpx.ConnectError("down")])
def test_timeouts_and_network_errors_are_unavailable(llm: GeminiLlm, error: Exception) -> None:
    respx.post(URL).mock(side_effect=error)
    with pytest.raises(LlmUnavailableError):
        llm.create(REQUEST)


@respx.mock
@pytest.mark.parametrize(
    "text",
    [
        "not json",
        "[]",
        "{}",
        '{"candidates": "x"}',
        '{"candidates": [{"content": {"parts": "x"}}]}',
        '{"candidates": [{"content": {"parts": [{"functionCall": {"args": {}}}]}}]}',
        '{"candidates": [{"content": {"parts": [{"functionCall": {"name": "f", "args": 1}}]}}]}',
    ],
)
def test_malformed_responses_are_unavailable(llm: GeminiLlm, text: str) -> None:
    respx.post(URL).respond(200, text=text)
    with pytest.raises(LlmUnavailableError):
        llm.create(REQUEST)


def test_unsupported_block_is_a_config_error(llm: GeminiLlm) -> None:
    image = {"type": "image", "source": {}}
    request = REQUEST.model_copy(update={"messages": [{"role": "user", "content": [image]}]})
    with pytest.raises(LlmConfigError):
        llm.create(request)


@respx.mock
@pytest.mark.parametrize("status", [200, 400, 429, 500])
def test_key_never_appears_in_logs_or_errors(
    llm: GeminiLlm, caplog: pytest.LogCaptureFixture, status: int
) -> None:
    body = reply([{"text": "ok"}]) if status == 200 else {"error": {"message": KEY}}
    respx.post(URL).respond(status, json=body)
    caplog.set_level(logging.DEBUG)
    try:
        llm.create(REQUEST)
    except (LlmUnavailableError, LlmConfigError) as error:
        assert KEY not in str(error)
    assert KEY not in caplog.text
