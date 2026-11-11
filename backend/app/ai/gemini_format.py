"""Child of gemini.py: LlmRequest → generateContent body (research R5). Pure, no I/O.

Mapping: system → systemInstruction; assistant → role "model"; tool_use → functionCall with its
id; tool_result → functionResponse (same id and name) in a "user" turn; document → inlineData;
output_schema → responseFormat.text JSON. A thoughtSignature that Gemini returned on a part is
kept on the block (SIGNATURE_KEY) and sent back on the same part, as Gemini 3 requires.
"""

import json
from typing import Any, Final

from app.ai.llm import LlmRequest
from app.common.constants import GEMINI_JSON_MIME, GEMINI_THINKING_LEVEL, LLM_MAX_TOKENS
from app.common.errors import LlmConfigError

SIGNATURE_KEY: Final = "gemini_thought_signature"
LOCAL_ID_PREFIX: Final = "paylens-call-"  # ids made by us when Gemini sent none; never sent back
ROLES: Final = {"user": "user", "assistant": "model"}
UNSUPPORTED_MESSAGE: Final = "This request has content the Gemini adapter cannot send."


def gemini_body(request: LlmRequest) -> dict[str, Any]:
    body: dict[str, Any] = {
        "systemInstruction": {"parts": [{"text": request.system}]},
        "contents": contents(request.messages),
        "generationConfig": generation_config(request),
    }
    if request.tools:
        body["tools"] = [{"functionDeclarations": [declaration(t) for t in request.tools]}]
    return body


def generation_config(request: LlmRequest) -> dict[str, Any]:
    config: dict[str, Any] = {
        "maxOutputTokens": LLM_MAX_TOKENS,
        "thinkingConfig": {"thinkingLevel": GEMINI_THINKING_LEVEL},
    }
    if request.output_schema is not None:
        schema = inline_refs(request.output_schema)
        config["responseFormat"] = {"text": {"mimeType": GEMINI_JSON_MIME, "schema": schema}}
    return config


def declaration(tool: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": tool["name"],
        "description": tool.get("description", ""),
        "parametersJsonSchema": inline_refs(tool["input_schema"]),
    }


def inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Replace local "#/$defs/X" references with their definitions (Gemini's docs do not promise
    $ref support for function parameters)."""
    definitions = schema.get("$defs", {})

    def resolve(node: Any) -> Any:
        if isinstance(node, dict):
            ref = node.get("$ref")
            if isinstance(ref, str) and ref.startswith("#/$defs/"):
                return resolve(definitions[ref.removeprefix("#/$defs/")])
            return {key: resolve(value) for key, value in node.items() if key != "$defs"}
        if isinstance(node, list):
            return [resolve(item) for item in node]
        return node

    resolved: dict[str, Any] = resolve(schema)
    return resolved


def contents(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    names: dict[str, str] = {}  # tool_use id → tool name, for the matching functionResponse
    turns: list[dict[str, Any]] = []
    for message in messages:
        content = message["content"]
        blocks = [{"type": "text", "text": content}] if isinstance(content, str) else content
        parts = [part(block, names) for block in blocks]
        turns.append({"role": ROLES[message["role"]], "parts": parts})
    return turns


def part(block: dict[str, Any], names: dict[str, str]) -> dict[str, Any]:
    kind = block.get("type")
    if kind == "text":
        return with_signature({"text": block.get("text", "")}, block)
    if kind == "tool_use":
        call_id, name = str(block.get("id", "")), str(block.get("name", ""))
        names[call_id] = name
        call = {"name": name, "args": block.get("input") or {}} | sent_id(call_id)
        return with_signature({"functionCall": call}, block)
    if kind == "tool_result":
        call_id = str(block.get("tool_use_id", ""))
        result = {"name": names.get(call_id, ""), "response": tool_response(block)}
        return {"functionResponse": result | sent_id(call_id)}
    if kind == "document":
        source = block["source"]
        return {"inlineData": {"mimeType": source["media_type"], "data": source["data"]}}
    raise LlmConfigError(UNSUPPORTED_MESSAGE)


def sent_id(call_id: str) -> dict[str, str]:
    return {} if not call_id or call_id.startswith(LOCAL_ID_PREFIX) else {"id": call_id}


def with_signature(gemini_part: dict[str, Any], block: dict[str, Any]) -> dict[str, Any]:
    signature = block.get(SIGNATURE_KEY)
    return gemini_part | {"thoughtSignature": signature} if signature else gemini_part


def tool_response(block: dict[str, Any]) -> dict[str, Any]:
    """functionResponse.response must be an object; failures use the documented "error" key."""
    content = block.get("content", "")
    if block.get("is_error"):
        return {"error": str(content)}
    try:
        value = json.loads(content) if isinstance(content, str) else content
    except json.JSONDecodeError:
        return {"output": content}
    return value if isinstance(value, dict) else {"output": value}
