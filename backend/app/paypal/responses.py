"""Reading PayPal response bodies safely: a non-JSON body is a rejected request, not a crash."""

import json
from typing import Any

import httpx

from app.common.errors import PayPalError

REJECTED_CODE = "PAYPAL_REJECTED"


def json_body(response: httpx.Response, message: str) -> Any:
    """Decode the JSON body; raise PayPalError(PAYPAL_REJECTED) with `message` if it is not JSON."""
    try:
        return json.loads(response.content)
    except ValueError as error:  # JSONDecodeError and UnicodeDecodeError
        raise PayPalError(message, code=REJECTED_CODE) from error


def issues(response: httpx.Response) -> set[str]:
    """PayPal error `details[].issue` values, or an empty set when the body has none."""
    try:
        payload = json.loads(response.content)
    except ValueError:
        return set()
    details = payload.get("details") if isinstance(payload, dict) else None
    if not isinstance(details, list):
        return set()
    return {str(d["issue"]) for d in details if isinstance(d, dict) and "issue" in d}
