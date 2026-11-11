"""Shared generateContent fakes for the Gemini tests (fake key and model; no network)."""

from typing import Any

BASE = "https://gemini.test"
KEY = "AQ.test-key-value"
MODEL = "gemini-test"
URL = f"{BASE}/v1beta/models/{MODEL}:generateContent"


def reply(parts: list[dict[str, Any]], finish: str | None = "STOP") -> dict[str, Any]:
    candidate: dict[str, Any] = {"content": {"role": "model", "parts": parts}, "index": 0}
    if finish is not None:
        candidate["finishReason"] = finish
    return {"candidates": [candidate], "usageMetadata": {"totalTokenCount": 10}}


def call_part(
    name: str, call_id: str | None, signature: str | None, args: dict[str, Any] | None = None
) -> dict[str, Any]:
    call: dict[str, Any] = {"name": name, "args": args or {"period": "all_time"}}
    if call_id is not None:
        call["id"] = call_id
    part: dict[str, Any] = {"functionCall": call}
    if signature is not None:
        part["thoughtSignature"] = signature
    return part
