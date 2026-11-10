"""In-memory fixed-window rate limiter per client IP (research R8).

Render runs one backend instance, so in-process counters are enough for the demo.
"""

import threading
import time
from collections.abc import Callable

from fastapi import Request

from app.common.constants import RATE_LIMIT_PRUNE_ABOVE
from app.common.errors import RateLimitedError

RATE_LIMITED_MESSAGE = "Too many requests. Please wait a moment and try again."

Clock = Callable[[], float]


class FixedWindowLimiter:
    """Allow `limit` hits per `window_s` seconds for each key."""

    def __init__(self, limit: int, window_s: int, clock: Clock = time.monotonic) -> None:
        self._limit = limit
        self._window_s = window_s
        self._clock = clock
        self._lock = threading.Lock()
        self._windows: dict[str, tuple[float, int]] = {}

    def hit(self, key: str) -> int | None:
        """Record one hit. Return None if allowed, else seconds until the window resets."""
        now = self._clock()
        with self._lock:
            if len(self._windows) > RATE_LIMIT_PRUNE_ABOVE:
                self._prune(now)
            started, count = self._windows.get(key, (now, 0))
            if now - started >= self._window_s:
                started, count = now, 0
            if count >= self._limit:
                return max(1, int(started + self._window_s - now + 0.999))
            self._windows[key] = (started, count + 1)
            return None

    def _prune(self, now: float) -> None:
        """Forget finished windows so many different keys cannot grow memory without limit."""
        expired = [
            k for k, (started, _) in self._windows.items() if now - started >= self._window_s
        ]
        for key in expired:
            del self._windows[key]

    def reset(self) -> None:
        with self._lock:
            self._windows.clear()


def client_ip(request: Request) -> str:
    """The client address. Behind a trusted proxy, uvicorn's ProxyHeadersMiddleware (added in
    main.py with FORWARDED_ALLOW_IPS) has already replaced it with the first untrusted address
    counted from the right of X-Forwarded-For, so client-sent (spoofed) entries never count."""
    return request.client.host if request.client else "unknown"


def check_rate_limit(limiter: FixedWindowLimiter, key: str) -> None:
    retry_after = limiter.hit(key)
    if retry_after is not None:
        raise RateLimitedError(RATE_LIMITED_MESSAGE, retry_after_s=retry_after)
