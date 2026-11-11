"""Frankfurter HTTP client: ECB reference rates, keyless (research R1, R2).

One attempt per call, no retry loop: FX is best-effort and must not delay sync or /pay.
"""

import json
import logging
from datetime import date
from decimal import Decimal
from http import HTTPStatus

import httpx
from pydantic import ValidationError

from app.common.constants import FX_PROVIDER, FX_SOURCE_NAME, INR
from app.common.errors import FxUnavailableError
from app.common.money import round_rate
from app.fx.gateway import FxQuote
from app.fx.schemas import FrankfurterRate

logger = logging.getLogger(__name__)

UNAVAILABLE_MESSAGE = "Exchange rates are not available right now."
NO_RATE_STATUSES = frozenset({HTTPStatus.BAD_REQUEST, HTTPStatus.NOT_FOUND, 422})


class FrankfurterGateway:
    def __init__(self, client: httpx.Client) -> None:
        self._client = client

    def mid_rate(self, currency: str, on: date) -> FxQuote | None:
        response = self._get(currency, on)
        if response.status_code in NO_RATE_STATUSES:
            return None
        if response.status_code != HTTPStatus.OK:
            logger.warning("FX source returned HTTP %d", response.status_code)
            raise FxUnavailableError(UNAVAILABLE_MESSAGE)
        parsed = self._parse(response.text)
        if parsed.base != currency or parsed.quote != INR or parsed.date > on:
            logger.warning("FX source answered a different question; ignoring it")
            raise FxUnavailableError(UNAVAILABLE_MESSAGE)
        return FxQuote(
            rate=round_rate(parsed.rate), published_date=parsed.date, source=FX_SOURCE_NAME
        )

    def _get(self, currency: str, on: date) -> httpx.Response:
        params = {"date": on.isoformat(), "providers": FX_PROVIDER}
        try:
            return self._client.get(f"/v2/rate/{currency}/{INR}", params=params)
        except httpx.HTTPError as error:
            logger.warning("FX source unreachable: %s", type(error).__name__)
            raise FxUnavailableError(UNAVAILABLE_MESSAGE) from error

    @staticmethod
    def _parse(text: str) -> FrankfurterRate:
        """Rates are JSON numbers: parse them straight to Decimal, never through float."""
        try:
            return FrankfurterRate.model_validate(json.loads(text, parse_float=Decimal))
        except (ValueError, ValidationError) as error:
            raise FxUnavailableError(UNAVAILABLE_MESSAGE) from error
