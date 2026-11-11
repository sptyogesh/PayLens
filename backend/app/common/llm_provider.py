"""Choose the LLM provider, model and URL from settings (003 research R5). Pure, no I/O.

A key is only ever sent to the company that issued it: when LLM_PROVIDER is set and the key prefix
clearly belongs to another provider, or the URL is another provider's, startup is refused.
Error messages name settings, never the key value.
"""

import re
from dataclasses import dataclass
from typing import Literal, cast
from urllib.parse import urlsplit

from app.common.constants import (
    LLM_DEFAULT_API_URLS,
    LLM_DEFAULT_MODELS,
    LLM_FALLBACK_PROVIDER,
    LLM_KEY_PREFIXES,
    LLM_MODEL_FAMILIES,
    LLM_MODEL_PATTERN,
)

LlmProvider = Literal["anthropic", "gemini"]


@dataclass(frozen=True)
class LlmChoice:
    provider: LlmProvider
    model: str
    api_url: str


def provider_of_key(api_key: str) -> str | None:
    """The provider whose key prefix `api_key` has, or None when the prefix is not known."""
    for provider, prefixes in LLM_KEY_PREFIXES.items():
        if api_key.startswith(prefixes):
            return provider
    return None


def choose_provider(provider: str, api_key: str) -> LlmProvider:
    from_key = provider_of_key(api_key)
    if provider and from_key and from_key != provider:
        raise ValueError(
            f"LLM_API_KEY looks like a {from_key} key but LLM_PROVIDER={provider}. "
            "Refusing to start so the key is not sent to the wrong provider."
        )
    if provider or from_key:
        return cast(LlmProvider, provider or from_key)  # both come from LLM_PROVIDERS names
    if api_key:
        raise ValueError(
            "Cannot tell the provider from LLM_API_KEY. Set LLM_PROVIDER to anthropic or gemini."
        )
    return LLM_FALLBACK_PROVIDER


def choose_model(provider: str, model: str) -> str:
    chosen = model or LLM_DEFAULT_MODELS[provider]
    if not re.fullmatch(LLM_MODEL_PATTERN, chosen):
        raise ValueError("LLM_MODEL has characters a model name cannot have")
    for other, family in LLM_MODEL_FAMILIES.items():
        if other != provider and chosen.lower().startswith(family):
            raise ValueError(f"LLM_MODEL={chosen} is a {other} model; the provider is {provider}")
    return chosen


def choose_api_url(provider: str, api_url: str) -> str:
    """Only the provider's own https host is accepted, so no URL variant (other host, http, extra
    path, user info, port, case) can carry the key elsewhere."""
    default = LLM_DEFAULT_API_URLS[provider]
    if not api_url:
        return default
    parts = urlsplit(api_url.strip())
    own = (parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), parts.query)
    if own != ("https", urlsplit(default).netloc, "", "") or parts.fragment:
        raise ValueError(f"LLM_API_URL must be {default} for the {provider} provider (or empty)")
    return default


def choose_llm(provider: str, api_key: str, model: str, api_url: str) -> LlmChoice:
    chosen = choose_provider(provider, api_key)
    return LlmChoice(chosen, choose_model(chosen, model), choose_api_url(chosen, api_url))
