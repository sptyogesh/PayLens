"""FastAPI dependencies shared by routers: settings, PayPal and FX gateways, rate limits."""

from collections.abc import Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from app.common.constants import FX_TIMEOUT_S
from app.common.http_client import make_client
from app.common.rate_limit import FixedWindowLimiter, check_rate_limit, client_ip
from app.config import Settings, get_settings
from app.fakes.fx_fake import FakeFxGateway
from app.fakes.paypal_fake import FakePayPalGateway
from app.fx import FrankfurterGateway, FxGateway
from app.paypal import HttpPayPalGateway, PayPalGateway, TokenCache

_limiters: dict[str, FixedWindowLimiter] = {}


@lru_cache
def get_gateway() -> PayPalGateway:
    settings = get_settings()
    if settings.paypal_mode == "fake":
        return FakePayPalGateway()
    client = make_client(settings.paypal_base_url)
    tokens = TokenCache(client, settings.paypal_client_id, settings.paypal_client_secret)
    return HttpPayPalGateway(client, tokens)


@lru_cache
def get_fx_gateway() -> FxGateway:
    settings = get_settings()
    if settings.fx_mode == "fake":
        return FakeFxGateway()
    return FrankfurterGateway(make_client(settings.fx_api_url, FX_TIMEOUT_S))


def get_limiter(name: str, limit_window: tuple[int, int]) -> FixedWindowLimiter:
    if name not in _limiters:
        _limiters[name] = FixedWindowLimiter(*limit_window)
    return _limiters[name]


def reset_limiters() -> None:
    """Used by tests to start each case with empty counters."""
    for limiter in _limiters.values():
        limiter.reset()


def rate_limit(name: str, limit_window: tuple[int, int]) -> Callable[..., None]:
    """Dependency factory: limit a route to `limit` requests per `window` seconds per IP."""

    def dependency(request: Request, settings: Annotated[Settings, Depends(get_settings)]) -> None:
        if not settings.rate_limit_enabled:
            return
        limiter = get_limiter(name, limit_window)
        check_rate_limit(limiter, client_ip(request, settings.trust_proxy_headers))

    return dependency
