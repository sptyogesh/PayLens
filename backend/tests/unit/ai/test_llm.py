"""AnthropicLlm against respx-mocked responses (never the real service)."""

import json
import logging

import httpx
import pytest
import respx

from app.ai.gemini import GeminiLlm
from app.ai.llm import AnthropicLlm, LlmRequest
from app.api.deps import get_llm
from app.common.constants import LLM_API_VERSION, LLM_BUSY_CODE, LLM_EFFORT, LLM_MAX_TOKENS
from app.common.errors import LlmConfigError, LlmUnavailableError
from app.fakes.llm_fake import FakeLlm

BASE = "https://llm.test"
URL = f"{BASE}/v1/messages"
SECRET = "sk-test-secret-value"
MODEL = "claude-test"
REQUEST = LlmRequest(
    system="rules",
    messages=[{"role": "user", "content": "hi"}],
    tools=[{"name": "income_summary", "description": "d", "input_schema": {"type": "object"}}],
)
OK_BODY = {
    "id": "msg_1",
    "type": "message",
    "role": "assistant",
    "content": [
        {"type": "thinking", "thinking": "", "signature": "sig"},
        {"type": "tool_use", "id": "toolu_1", "name": "income_summary", "input": {}},
    ],
    "stop_reason": "tool_use",
}


@pytest.fixture
def llm() -> AnthropicLlm:
    return AnthropicLlm(httpx.Client(base_url=BASE), SECRET, MODEL)


@respx.mock
def test_success_parses_blocks_and_sends_the_contract_body(llm: AnthropicLlm) -> None:
    route = respx.post(URL).respond(200, json=OK_BODY)
    response = llm.create(REQUEST)
    assert response.stop_reason == "tool_use"
    assert response.content == OK_BODY["content"]
    sent = route.calls.last.request
    assert sent.headers["x-api-key"] == SECRET
    assert sent.headers["anthropic-version"] == LLM_API_VERSION
    assert sent.headers["content-type"] == "application/json"
    body = json.loads(sent.content)
    assert body == {
        "model": MODEL,
        "max_tokens": LLM_MAX_TOKENS,
        "system": "rules",
        "messages": REQUEST.messages,
        "tools": REQUEST.tools,
        "output_config": {"effort": LLM_EFFORT},
    }
    for rejected in ("temperature", "top_p", "thinking", "tool_choice"):
        assert rejected not in body


@respx.mock
@pytest.mark.parametrize("status", [429, 500, 502, 503, 529])
def test_temporary_statuses_are_unavailable(llm: AnthropicLlm, status: int) -> None:
    respx.post(URL).respond(status, json={"type": "error"})
    with pytest.raises(LlmUnavailableError) as caught:
        llm.create(REQUEST)
    assert (caught.value.code == LLM_BUSY_CODE) is (status == 429)


@respx.mock
@pytest.mark.parametrize("status", [400, 401, 403, 404, 413])
def test_rejected_requests_are_config_errors(llm: AnthropicLlm, status: int) -> None:
    respx.post(URL).respond(status, json={"type": "error"})
    with pytest.raises(LlmConfigError):
        llm.create(REQUEST)


@respx.mock
@pytest.mark.parametrize(
    "error", [httpx.ReadTimeout("slow"), httpx.ConnectError("down"), httpx.ConnectTimeout("x")]
)
def test_timeouts_and_network_errors_are_unavailable(llm: AnthropicLlm, error: Exception) -> None:
    respx.post(URL).mock(side_effect=error)
    with pytest.raises(LlmUnavailableError):
        llm.create(REQUEST)


@respx.mock
@pytest.mark.parametrize("text", ["not json", '{"content": "wrong"}', "{}"])
def test_unreadable_responses_are_unavailable(llm: AnthropicLlm, text: str) -> None:
    respx.post(URL).respond(200, text=text)
    with pytest.raises(LlmUnavailableError):
        llm.create(REQUEST)


@respx.mock
@pytest.mark.parametrize("status", [200, 401, 500])
def test_key_never_appears_in_logs(
    llm: AnthropicLlm, caplog: pytest.LogCaptureFixture, status: int
) -> None:
    respx.post(URL).respond(status, json=OK_BODY if status == 200 else {"error": SECRET})
    caplog.set_level(logging.DEBUG)
    try:
        llm.create(REQUEST)
    except (LlmUnavailableError, LlmConfigError) as error:
        assert SECRET not in str(error)
    assert SECRET not in caplog.text


def test_get_llm_is_the_fake_in_tests() -> None:
    get_llm.cache_clear()
    assert isinstance(get_llm(), FakeLlm)
    get_llm.cache_clear()


@pytest.mark.parametrize(
    ("provider", "key", "client_type"),
    [
        ("anthropic", SECRET, AnthropicLlm),
        ("", "sk-ant-test-1", AnthropicLlm),
        ("gemini", "gemini-test-key", GeminiLlm),
        ("", "AQ.test-1", GeminiLlm),
    ],
)
def test_get_llm_http_mode_builds_the_chosen_provider(
    monkeypatch: pytest.MonkeyPatch, provider: str, key: str, client_type: type
) -> None:
    monkeypatch.setenv("LLM_MODE", "http")
    monkeypatch.setenv("LLM_PROVIDER", provider)
    monkeypatch.setenv("LLM_API_KEY", key)
    get_llm.cache_clear()
    try:
        assert isinstance(get_llm(), client_type)
    finally:
        get_llm.cache_clear()
