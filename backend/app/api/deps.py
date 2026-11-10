"""FastAPI dependencies shared by routers: settings, PayPal, FX and LLM gateways, rate limits."""

from collections.abc import Callable
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Request

from app.ai.llm import AnthropicLlm, LlmClient
from app.common.constants import FX_TIMEOUT_S, LLM_TIMEOUT_S
from app.common.http_client import make_client
from app.common.rate_limit import FixedWindowLimiter, check_rate_limit, client_ip
from app.config import Settings, get_settings
from app.fakes.fx_fake import FakeFxGateway
from app.fakes.llm_fake import FakeLlm
from app.fakes.paypal_fake import FakePayPalGateway
from app.fx import FrankfurterGateway, FxGateway
from app.paypal import HttpPayPalGateway, PayPalGateway, TokenCache

__all__ = ["get_fx_gateway", "get_gateway", "get_llm", "rate_limit", "reset_limiters"]

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


@lru_cache
def get_llm() -> LlmClient:
    """The fake LLM in tests and E2E (LLM_MODE=fake); the Anthropic client otherwise."""
    settings = get_settings()
    if settings.llm_mode == "fake":
        return FakeLlm()
    client = make_client(settings.llm_api_url, LLM_TIMEOUT_S)
    return AnthropicLlm(client, settings.llm_api_key, settings.llm_model)


def get_limiter(name: str, limit_window: tuple[int, int]) -> FixedWindowLimiter:
    if name not in _limiters:
        _limiters[name] = FixedWindowLimiter(*limit_window)
    return _limiters[name]


def reset_limiters() -> None:
    """Used by tests to start each case with empty counters."""
    for limiter in _limiters.values():
        limiter.reset()


GLOBAL_KEY = "*"


def rate_limit(
    name: str, limit_window: tuple[int, int], global_window: tuple[int, int] | None = None
) -> Callable[..., None]:
    """Dependency factory: `limit` requests per `window` seconds per IP, and optionally one shared
    cap for all clients together (LLM routes: a spoofed or rotating IP cannot run up the bill)."""

    def dependency(request: Request, settings: Annotated[Settings, Depends(get_settings)]) -> None:
        if not settings.rate_limit_enabled:
            return
        if global_window is not None:
            check_rate_limit(get_limiter(f"{name}:all", global_window), GLOBAL_KEY)
        limiter = get_limiter(name, limit_window)
        check_rate_limit(limiter, client_ip(request, settings.trust_proxy_headers))

    return dependency
