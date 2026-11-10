"""Read one FIRA PDF with the LLM into a strict schema, then check it in code (004 FR-002, FR-003).

The LLM only copies fields; code validates them (E1-E4). LlmUnavailableError and LlmConfigError
propagate to the caller. The document bytes and the model output are never logged.
"""

import base64
import json
import logging
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any, Final

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from app.ai.llm import LlmClient, LlmRequest
from app.ai.prompts import load_prompt
from app.common.constants import (
    FIRA_AMOUNT_MAX,
    FIRA_INR_TOLERANCE_PCT,
    FIRA_PDF_MEDIA_TYPE,
    FIRA_PURPOSE_CODE_MAX,
    FIRA_RATE_MAX,
    FIRA_REFERENCE_MAX,
    FIRA_REMITTER_MAX,
    LLM_TIMEOUT_S,
)
from app.common.errors import AppError
from app.common.money import parse_money
from app.engine.fira_match import within_pct

logger = logging.getLogger(__name__)

PROMPT_FILE: Final = "fira_extract.md"
INSTRUCTION: Final = "Extract the FIRA fields from the attached document into the JSON schema."
ISO_CURRENCY: Final = re.compile(r"^[A-Z]{3}$")
UNREADABLE_MESSAGE: Final = "The AI reader returned something that is not a FIRA record."
REQUIRED: Final = {
    "foreign_amount": "Missing foreign amount",
    "currency": "Missing currency",
    "remittance_date": "Missing remittance date",
}
POSITIVE: Final = {
    "foreign_amount": "Foreign amount must be more than 0",
    "inr_amount": "INR amount must be more than 0",
    "rate": "Rate must be more than 0",
}
BAD_CURRENCY: Final = "Currency is not a 3-letter ISO code"
INR_MISMATCH: Final = (
    f"INR amount is not foreign amount × rate (more than {FIRA_INR_TOLERANCE_PCT}% off)"
)
FIELD_HINTS: Final = {
    "foreign_amount": "Amount in the foreign currency as a decimal string, e.g. 1200.00.",
    "currency": "3-letter ISO 4217 currency code in capitals, e.g. USD.",
    "inr_amount": "Amount credited in INR as a decimal string.",
    "rate": "INR per one unit of the foreign currency, as a decimal string.",
    "remittance_date": "Date of the remittance as YYYY-MM-DD.",
    "reference_no": "Remittance or transaction reference exactly as printed.",
    "remitter": "Name of the sender.",
    "purpose_code": "RBI purpose code, e.g. P0802.",
}


TOO_LARGE_AMOUNT: Final = "Amount is too large to be real"
BAD_RATE: Final = "Exchange rate is not plausible"
TEXT_LIMITS: Final = {
    "reference_no": (FIRA_REFERENCE_MAX, "Reference is too long (shortened)"),
    "remitter": (FIRA_REMITTER_MAX, "Remitter is too long (shortened)"),
    "purpose_code": (FIRA_PURPOSE_CODE_MAX, "Purpose code is too long (shortened)"),
}


class FiraExtractionError(AppError):
    """The LLM output was not JSON or did not match the schema (E4). Nothing is stored."""

    http_status = 502
    code = "FIRA_EXTRACTION_FAILED"


class FiraExtraction(BaseModel):
    """Every field is present; null means the document did not show it. Floats are rejected."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    foreign_amount: Decimal | None
    currency: str | None
    inr_amount: Decimal | None
    rate: Decimal | None
    remittance_date: date | None
    reference_no: str | None
    remitter: str | None
    purpose_code: str | None

    @field_validator("foreign_amount", "inr_amount", "rate", mode="before")
    @classmethod
    def decimal_from_string(cls, value: object) -> Decimal | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError("amounts must be decimal strings")
        return parse_money(value)


def output_schema() -> dict[str, Any]:
    """Strict JSON schema for the LLM: all fields required, each a string or null."""
    properties = {
        name: {"anyOf": [{"type": "string"}, {"type": "null"}], "description": hint}
        for name, hint in FIELD_HINTS.items()
    }
    return {
        "type": "object",
        "properties": properties,
        "required": list(FIELD_HINTS),
        "additionalProperties": False,
    }


EXTRACTION_SCHEMA: Final = output_schema()


@dataclass(frozen=True)
class ExtractionOutcome:
    """The parsed fields and the validation problems (empty when the FIRA is consistent)."""

    extraction: FiraExtraction
    problems: list[str]


def build_request(pdf_bytes: bytes) -> LlmRequest:
    document = {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": FIRA_PDF_MEDIA_TYPE,
            "data": base64.b64encode(pdf_bytes).decode("ascii"),
        },
    }
    content = [document, {"type": "text", "text": INSTRUCTION}]
    return LlmRequest(
        system=load_prompt(PROMPT_FILE),
        messages=[{"role": "user", "content": content}],
        timeout_s=LLM_TIMEOUT_S,
        output_schema=EXTRACTION_SCHEMA,
    )


def parse_output(content: list[dict[str, Any]]) -> FiraExtraction:
    text = next((b.get("text") for b in content if b.get("type") == "text"), None)
    if not isinstance(text, str):
        raise FiraExtractionError(UNREADABLE_MESSAGE)
    try:
        return FiraExtraction.model_validate(json.loads(text))
    except (json.JSONDecodeError, ValidationError) as error:
        raise FiraExtractionError(UNREADABLE_MESSAGE) from error


def extract(llm: LlmClient, pdf_bytes: bytes, file_name: str) -> ExtractionOutcome:
    """One LLM call with the PDF as a document block (E1). Raises FiraExtractionError (E4)."""
    response = llm.create(build_request(pdf_bytes))
    try:
        extraction = parse_output(response.content)
    except FiraExtractionError:
        logger.warning("FIRA extraction output unreadable (file name length %d)", len(file_name))
        raise
    return ExtractionOutcome(extraction=extraction, problems=validate(extraction))


def validate(extraction: FiraExtraction) -> list[str]:
    """Reasons the FIRA cannot be matched as is (E2, E3); empty when it is consistent."""
    values = extraction.model_dump()
    problems = [text for name, text in REQUIRED.items() if values[name] is None]
    problems += [
        text for name, text in POSITIVE.items() if values[name] is not None and values[name] <= 0
    ]
    if extraction.currency is not None and not ISO_CURRENCY.match(extraction.currency):
        problems.append(BAD_CURRENCY)
    problems += [
        TOO_LARGE_AMOUNT
        for value in (extraction.foreign_amount, extraction.inr_amount)
        if value is not None and value > FIRA_AMOUNT_MAX
    ]
    if extraction.rate is not None and not Decimal(0) < extraction.rate <= FIRA_RATE_MAX:
        problems.append(BAD_RATE)
    problems += [
        text for name, (limit, text) in TEXT_LIMITS.items() if len(values[name] or "") > limit
    ]
    if not problems and not inr_consistent(extraction):
        problems.append(INR_MISMATCH)
    return problems


def inr_consistent(extraction: FiraExtraction) -> bool:
    """|inr − amount × rate| within the tolerance; skipped when INR or the rate is missing."""
    amount, inr, rate = extraction.foreign_amount, extraction.inr_amount, extraction.rate
    if amount is None or inr is None or rate is None:
        return True
    return within_pct(inr, amount * rate, FIRA_INR_TOLERANCE_PCT)
