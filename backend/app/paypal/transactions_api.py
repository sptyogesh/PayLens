"""One Transaction Search page: GET /v1/reporting/transactions (research R4)."""

from collections.abc import Callable
from datetime import datetime
from typing import Any

import httpx
from pydantic import ValidationError

from app.common.constants import PAYPAL_PAGE_SIZE
from app.common.dates import ensure_utc
from app.common.errors import PayPalError
from app.paypal.dto import SearchPage, SearchRow
from app.paypal.responses import json_body
from app.paypal.schemas import SearchResponse

SEARCH_PATH = "/v1/reporting/transactions"
REJECTED_MESSAGE = (
    "PayPal refused the Transaction Search request. "
    "Check that Transaction Search is enabled for the sandbox app."
)

Request = Callable[..., httpx.Response]


def paypal_date(value: datetime) -> str:
    return ensure_utc(value).strftime("%Y-%m-%dT%H:%M:%SZ")


def search_params(start: datetime, end: datetime, page: int) -> dict[str, str | int]:
    return {
        "start_date": paypal_date(start),
        "end_date": paypal_date(end),
        "fields": "all",
        "balance_affecting_records_only": "N",
        "page_size": PAYPAL_PAGE_SIZE,
        "page": page,
    }


UNEXPECTED_FORMAT_MESSAGE = "PayPal returned transaction data in an unexpected format."


def parse_page(payload: Any) -> SearchPage:
    try:
        response = SearchResponse.model_validate(payload)
    except ValidationError as error:
        raise PayPalError(UNEXPECTED_FORMAT_MESSAGE, code="PAYPAL_REJECTED") from error
    raw_rows: list[dict[str, Any]] = payload.get("transaction_details") or []
    rows = [
        SearchRow(detail, raw)
        for detail, raw in zip(response.transaction_details, raw_rows, strict=True)
    ]
    return SearchPage(rows=rows, page=response.page, total_pages=response.total_pages)


def fetch_page(request: Request, start: datetime, end: datetime, page: int) -> SearchPage:
    response = request("GET", SEARCH_PATH, params=search_params(start, end, page))
    if response.status_code != httpx.codes.OK:
        raise PayPalError(REJECTED_MESSAGE, code="PAYPAL_REJECTED")
    return parse_page(json_body(response, UNEXPECTED_FORMAT_MESSAGE))
