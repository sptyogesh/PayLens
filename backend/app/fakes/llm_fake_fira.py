"""Fake LLM helpers for FIRA (004 research R2): extraction from the embedded marker, chat answer.

Generated demo PDFs carry their true fields as `PAYLENS-FAKE-FIRA:{json}` in the PDF /Subject
metadata. The fake "reads" a PDF by finding that marker in the document bytes. A marker with
"fake_mode": "non_json" answers plain text (E4); "fake_mode": "fail" raises (AI down).
"""

import base64
import json
import re
from typing import Any, Final

from app.ai.llm import LlmRequest
from app.common.constants import FIRA_FAKE_MARKER
from app.common.errors import LlmUnavailableError

MARKER: Final = re.compile(re.escape(FIRA_FAKE_MARKER.encode()) + rb"(\{.*?\})", re.DOTALL)
PDF_ESCAPES: Final = ((rb"\(", b"("), (rb"\)", b")"), (rb"\\", b"\\"))
FAKE_MODE_KEY: Final = "fake_mode"
NON_JSON_TEXT: Final = "I could not read this"
FIELDS: Final = (
    "foreign_amount",
    "currency",
    "inr_amount",
    "rate",
    "remittance_date",
    "reference_no",
    "remitter",
    "purpose_code",
)


def document_bytes(request: LlmRequest) -> bytes:
    for message in request.messages:
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if block.get("type") == "document":
                return base64.b64decode(block["source"]["data"])
    return b""


def read_marker(pdf: bytes) -> dict[str, Any] | None:
    found = MARKER.search(pdf)
    if found is None:
        return None
    raw = found.group(1)
    for escaped, plain in PDF_ESCAPES:
        raw = raw.replace(escaped, plain)
    data = json.loads(raw)
    return data if isinstance(data, dict) else None


def extraction_text(request: LlmRequest) -> str:
    """The text block the fake returns for an extraction request (raises when told to fail)."""
    marker = read_marker(document_bytes(request)) or {}
    mode = marker.pop(FAKE_MODE_KEY, None)
    if mode == "fail":
        raise LlmUnavailableError("Fake LLM is down.")
    if mode == "non_json":
        return NON_JSON_TEXT
    fields: dict[str, Any] = dict.fromkeys(FIELDS)
    fields.update(marker)
    return json.dumps(fields)


def payment_line(item: dict[str, Any]) -> str:
    gross = item["gross"]
    return f"{item['date']} {item['client']} {gross['currency']} {gross['amount']}"


def describe_fira(result: dict[str, Any], period: str) -> str:
    """fira_status answer: counts, then the missing and needs-review payments copied verbatim."""
    parts = [
        f"For {period}: matched {result['matched_count']},"
        f" needs review {result['needs_review_count']}, missing {result['missing_count']}."
    ]
    if result["missing"]:
        parts.append("Missing a FIRA: " + "; ".join(map(payment_line, result["missing"])) + ".")
    if result["needs_review"]:
        lines = "; ".join(map(payment_line, result["needs_review"]))
        parts.append("Needs review: " + lines + ".")
    return " ".join(parts)
