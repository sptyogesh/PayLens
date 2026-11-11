"""Builders for FIRA tests: demo PDFs whose /Subject marker tells the fake LLM what to return."""

from typing import Any

from scripts.generate_fira_samples import fira_pdf_bytes

VALID_FIELDS: dict[str, Any] = {
    "foreign_amount": "1000.00",
    "currency": "USD",
    "inr_amount": "84000.00",
    "rate": "84.000000",
    "remittance_date": "2026-11-08",
    "reference_no": "TX-1",
    "remitter": "PayPal (demo)",
    "purpose_code": "P0802",
}


def fields(**overrides: Any) -> dict[str, Any]:
    return {**VALID_FIELDS, **overrides}


def fira_pdf(extra_lines: tuple[str, ...] = (), **overrides: Any) -> bytes:
    """A demo FIRA PDF; `None` overrides drop the field so the fake returns it as null."""
    found = {key: value for key, value in fields(**overrides).items() if value is not None}
    return fira_pdf_bytes(found, extra_lines)
