"""Provider selection (research R5): LLM_PROVIDER, key-prefix detection, mismatch refusal, defaults.

Keys here are short fakes (never the real key; tests do not read backend/.env).
"""

import pytest
from pydantic import ValidationError

from app.common.constants import LLM_DEFAULT_API_URLS, LLM_DEFAULT_MODELS
from app.common.llm_provider import choose_llm, provider_of_key
from app.config import Settings

DB = "postgresql://u:p@h/db"
ANTHROPIC_KEY = "sk-ant-test-1"
GEMINI_KEY = "AIza-test-1"
GEMINI_AUTH_KEY = "AQ.test-1"


def http_settings(**values: str) -> Settings:
    base = {"app_env": "test", "paypal_mode": "fake", "fx_mode": "fake", "llm_mode": "http"}
    return Settings.model_validate({"database_url": DB, **base, **values})


@pytest.mark.parametrize(
    ("key", "provider"),
    [
        (ANTHROPIC_KEY, "anthropic"),
        (GEMINI_KEY, "gemini"),
        (GEMINI_AUTH_KEY, "gemini"),
        ("other-key", None),
        ("", None),
    ],
)
def test_provider_is_detected_from_the_key_prefix(key: str, provider: str | None) -> None:
    assert provider_of_key(key) == provider


@pytest.mark.parametrize(
    ("key", "provider"), [(ANTHROPIC_KEY, "anthropic"), (GEMINI_KEY, "gemini")]
)
def test_empty_provider_uses_the_detected_one_with_its_defaults(key: str, provider: str) -> None:
    settings = http_settings(llm_api_key=key)
    assert settings.llm_provider == provider
    assert settings.llm_model == LLM_DEFAULT_MODELS[provider]
    assert settings.llm_api_url == LLM_DEFAULT_API_URLS[provider]


def test_gemini_default_model_is_the_free_tier_flash_model() -> None:
    assert http_settings(llm_api_key=GEMINI_AUTH_KEY).llm_model == "gemini-3.6-flash"


def test_set_provider_wins_for_an_unknown_key_format() -> None:
    settings = http_settings(llm_provider="gemini", llm_api_key="new-format-key")
    assert (settings.llm_provider, settings.llm_model) == ("gemini", "gemini-3.6-flash")


@pytest.mark.parametrize(
    ("provider", "key"), [("gemini", ANTHROPIC_KEY), ("anthropic", GEMINI_KEY)]
)
def test_key_of_another_provider_is_refused_without_showing_it(provider: str, key: str) -> None:
    with pytest.raises(ValidationError, match="not sent to the wrong provider") as caught:
        http_settings(llm_provider=provider, llm_api_key=key)
    assert key not in str(caught.value)


def test_no_settings_error_echoes_secret_values() -> None:
    with pytest.raises(ValidationError) as caught:
        http_settings(llm_api_key="other-key", paypal_client_secret="paypal-secret-1")
    assert "other-key" not in str(caught.value)
    assert "paypal-secret-1" not in str(caught.value)


def test_mismatch_message_never_contains_the_key() -> None:
    with pytest.raises(ValueError, match="wrong provider") as caught:
        choose_llm("gemini", ANTHROPIC_KEY, "", "")
    assert ANTHROPIC_KEY not in str(caught.value)


def test_unknown_key_without_provider_is_refused() -> None:
    with pytest.raises(ValidationError, match="Set LLM_PROVIDER"):
        http_settings(llm_api_key="other-key")


def test_set_model_is_kept() -> None:
    assert http_settings(llm_api_key=GEMINI_KEY, llm_model="gemini-3.8-flash").llm_model == (
        "gemini-3.8-flash"
    )


@pytest.mark.parametrize(
    ("key", "model"), [(GEMINI_KEY, "claude-opus-5-5"), (ANTHROPIC_KEY, "gemini-3.8-flash")]
)
def test_model_of_another_provider_is_refused(key: str, model: str) -> None:
    with pytest.raises(ValidationError, match="model; the provider is"):
        http_settings(llm_api_key=key, llm_model=model)


@pytest.mark.parametrize("model", ["gemini/../x", "gemini 3", "gemini?key=1", "-gemini"])
def test_model_names_that_could_change_the_url_are_refused(model: str) -> None:
    with pytest.raises(ValidationError, match="characters a model name cannot have"):
        http_settings(llm_api_key=GEMINI_KEY, llm_model=model)


@pytest.mark.parametrize(
    ("key", "url"),
    [
        (GEMINI_KEY, "https://api.anthropic.com/"),
        (ANTHROPIC_KEY, LLM_DEFAULT_API_URLS["gemini"]),
        (ANTHROPIC_KEY, "https://generativelanguage.googleapis.com/v1beta"),
        (ANTHROPIC_KEY, "https://GenerativeLanguage.googleapis.com"),
        (GEMINI_KEY, "https://api.anthropic.com/v1"),
        (GEMINI_KEY, "http://generativelanguage.googleapis.com"),
        (GEMINI_KEY, "https://generativelanguage.googleapis.com.evil.test"),
        (GEMINI_KEY, "https://user@generativelanguage.googleapis.com"),
        (GEMINI_KEY, "https://generativelanguage.googleapis.com:8443"),
        (GEMINI_KEY, "https://generativelanguage.googleapis.com/?x=1"),
        (GEMINI_KEY, "https://llm.example"),
    ],
)
def test_only_the_providers_own_https_url_is_accepted(key: str, url: str) -> None:
    with pytest.raises(ValidationError, match="LLM_API_URL must be"):
        http_settings(llm_api_key=key, llm_api_url=url)


@pytest.mark.parametrize("url", ["https://GENERATIVELANGUAGE.googleapis.com/", ""])
def test_own_url_in_any_case_is_normalised(url: str) -> None:
    settings = http_settings(llm_api_key=GEMINI_KEY, llm_api_url=url)
    assert settings.llm_api_url == LLM_DEFAULT_API_URLS["gemini"]


@pytest.mark.parametrize(
    "padded", [f" {ANTHROPIC_KEY}", f"{ANTHROPIC_KEY}\n", f"\t{ANTHROPIC_KEY} "]
)
def test_whitespace_around_the_key_cannot_hide_its_prefix(padded: str) -> None:
    with pytest.raises(ValidationError, match="wrong provider"):
        http_settings(llm_provider="gemini", llm_api_key=padded)
    assert http_settings(llm_api_key=padded).llm_api_key == ANTHROPIC_KEY


def test_blank_key_counts_as_missing() -> None:
    with pytest.raises(ValidationError, match="LLM_API_KEY is required"):
        http_settings(llm_api_key="   ")


def test_fake_mode_without_a_key_still_starts() -> None:
    settings = Settings(app_env="test", paypal_mode="fake", llm_mode="fake", database_url=DB)
    assert settings.llm_provider == "anthropic"
