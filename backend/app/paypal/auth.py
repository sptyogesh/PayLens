"""OAuth access token with caching (Principle VIII): reused until shortly before expiry."""

import threading
import time
from collections.abc import Callable

import httpx

from app.common.constants import PAYPAL_TOKEN_REFRESH_MARGIN_S
from app.common.errors import PayPalError
from app.common.http_client import send_with_retry
from app.paypal.schemas import TokenResponse

OAUTH_ENDPOINT = "/v1/oauth2/token"
AUTH_FAILED_MESSAGE = "PayPal rejected the app credentials. Check the sandbox client ID and secret."

Clock = Callable[[], float]


class TokenCache:
    def __init__(
        self, client: httpx.Client, client_id: str, secret: str, clock: Clock = time.monotonic
    ) -> None:
        self._client = client
        self._auth = (client_id, secret)
        self._clock = clock
        self._lock = threading.Lock()
        self._token: str | None = None
        self._expires_at = 0.0

    def get(self) -> str:
        with self._lock:
            if self._token is None or self._clock() >= self._expires_at:
                self._token, self._expires_at = self._fetch()
            return self._token

    def invalidate(self) -> None:
        with self._lock:
            self._token = None

    def _fetch(self) -> tuple[str, float]:
        response = send_with_retry(
            lambda: self._client.post(
                OAUTH_ENDPOINT, data={"grant_type": "client_credentials"}, auth=self._auth
            )
        )
        if response.status_code != httpx.codes.OK:
            raise PayPalError(AUTH_FAILED_MESSAGE, code="PAYPAL_AUTH_FAILED")
        token = TokenResponse.model_validate_json(response.content)
        lifetime = max(0, token.expires_in - PAYPAL_TOKEN_REFRESH_MARGIN_S)
        return token.access_token, self._clock() + lifetime
