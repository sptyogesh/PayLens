"""One outbound HTTP client with timeout and retry (Principle VIII).

429 and 5xx are retried with exponential backoff; other 4xx are returned to the caller.
"""

import logging
import time
from collections.abc import Callable

import httpx

from app.common.constants import (
    HTTP_BACKOFF_BASE_S,
    HTTP_MAX_RETRIES,
    HTTP_RETRY_STATUSES,
    HTTP_TIMEOUT_S,
)
from app.common.errors import PayPalError

logger = logging.getLogger(__name__)

UNAVAILABLE_MESSAGE = "PayPal is not responding right now. Please try again in a minute."

Sleep = Callable[[float], None]


def make_client(base_url: str, timeout_s: float = HTTP_TIMEOUT_S) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=timeout_s)


def backoff_delay(attempt: int) -> float:
    """Delay before retry number `attempt` (0-based): 1 s, 2 s, 4 s, ..."""
    return float(HTTP_BACKOFF_BASE_S * (2**attempt))


def send_with_retry(
    send: Callable[[], httpx.Response], sleep: Sleep | None = None
) -> httpx.Response:
    """Call `send`, retrying 429/5xx and network errors up to HTTP_MAX_RETRIES times."""
    for attempt in range(HTTP_MAX_RETRIES + 1):
        try:
            response = send()
        except httpx.TransportError as error:
            logger.warning(
                "HTTP transport error (attempt %d): %s", attempt + 1, type(error).__name__
            )
        else:
            if response.status_code not in HTTP_RETRY_STATUSES:
                return response
            logger.warning("HTTP %d (attempt %d)", response.status_code, attempt + 1)
        if attempt < HTTP_MAX_RETRIES:
            (sleep or time.sleep)(backoff_delay(attempt))
    raise PayPalError(UNAVAILABLE_MESSAGE, code="PAYPAL_UNAVAILABLE")
