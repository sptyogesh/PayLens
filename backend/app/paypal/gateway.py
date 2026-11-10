"""PayPal gateway: the Protocol every adapter implements, and the real HTTP adapter.

Each user story adds its methods (US1: search, US2: orders). Tests and E2E use the
FakePayPalGateway from app.fakes, which is only allowed when APP_ENV=test.
"""

from datetime import datetime
from typing import Any, Protocol

import httpx

from app.common.errors import PayPalError
from app.common.http_client import send_with_retry
from app.paypal.auth import AUTH_FAILED_MESSAGE, TokenCache
from app.paypal.dto import SearchPage
from app.paypal.transactions_api import fetch_page


class PayPalGateway(Protocol):
    """Operations PayLens needs from PayPal."""

    def search_transactions(self, start: datetime, end: datetime, page: int) -> SearchPage: ...


class HttpPayPalGateway:
    """Calls the PayPal sandbox REST API."""

    def __init__(self, client: httpx.Client, token_cache: TokenCache) -> None:
        self._client = client
        self._tokens = token_cache

    def search_transactions(self, start: datetime, end: datetime, page: int) -> SearchPage:
        return fetch_page(self.request, start, end, page)

    def request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        """Send with a bearer token. On 401: refresh the token once and retry (Principle VIII)."""
        response = self._send(method, path, **kwargs)
        if response.status_code == httpx.codes.UNAUTHORIZED:
            self._tokens.invalidate()
            response = self._send(method, path, **kwargs)
            if response.status_code == httpx.codes.UNAUTHORIZED:
                raise PayPalError(AUTH_FAILED_MESSAGE, code="PAYPAL_AUTH_FAILED")
        return response

    def _send(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        headers = {**kwargs.pop("headers", {}), "Authorization": f"Bearer {self._tokens.get()}"}
        return send_with_retry(
            lambda: self._client.request(method, path, headers=headers, **kwargs)
        )
