"""AnthropicLlm sends strict JSON output and the PDF document block (004 research R1; respx)."""

import json

import httpx
import respx

from app.ai.fira_extract import EXTRACTION_SCHEMA, build_request, extract
from app.ai.llm import AnthropicLlm
from app.common.constants import FIRA_PDF_MEDIA_TYPE, LLM_EFFORT
from tests.fixtures.fira import VALID_FIELDS

BASE = "https://llm.test"
URL = f"{BASE}/v1/messages"


def ok_body(text: str) -> dict[str, object]:
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": text}],
        "stop_reason": "end_turn",
    }


@respx.mock
def test_extraction_request_body_has_format_document_and_no_tools() -> None:
    route = respx.post(URL).respond(200, json=ok_body(json.dumps(VALID_FIELDS)))
    llm = AnthropicLlm(httpx.Client(base_url=BASE), "sk-test", "claude-test")
    outcome = extract(llm, b"%PDF-1.4 demo", "fira.pdf")
    assert outcome.problems == []
    body = json.loads(route.calls.last.request.content)
    assert body["output_config"] == {
        "effort": LLM_EFFORT,
        "format": {"type": "json_schema", "schema": EXTRACTION_SCHEMA},
    }
    assert "tools" not in body
    document, instruction = body["messages"][0]["content"]
    assert document == {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": FIRA_PDF_MEDIA_TYPE,
            "data": build_request(b"%PDF-1.4 demo").messages[0]["content"][0]["source"]["data"],
        },
    }
    assert instruction["type"] == "text" and instruction["text"]
