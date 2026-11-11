"""LLM providers behind the single wrapper (003 research R1, R5: Gemini adapter)."""

from typing import Final

LLM_PROVIDERS: Final = ("anthropic", "gemini")
# Used only when there is no key at all (LLM_MODE=fake in tests); http mode always needs a key.
LLM_FALLBACK_PROVIDER: Final = "anthropic"
# Key prefixes that identify a provider. Gemini: "AIza" = standard API keys, "AQ." = the auth keys
# AI Studio creates by default since 28 May 2026 (observed format; Google does not document it).
LLM_KEY_PREFIXES: Final = {"anthropic": ("sk-ant-",), "gemini": ("AIza", "AQ.")}
# Model names start with the provider's family; a model of the other provider is refused.
LLM_MODEL_FAMILIES: Final = {"anthropic": "claude", "gemini": "gemini"}
LLM_DEFAULT_MODELS: Final = {
    "anthropic": "claude-opus-5-5",
    # Stable, free tier, function calling + PDF input + structured outputs (research R5).
    "gemini": "gemini-3.6-flash",
}
LLM_DEFAULT_API_URLS: Final = {
    "anthropic": "https://api.anthropic.com",
    "gemini": "https://generativelanguage.googleapis.com",
}
LLM_MODEL_PATTERN: Final = r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$"  # also safe inside a URL path
LLM_BUSY_CODE: Final = "LLM_BUSY"  # HTTP 429: rate limit or free-tier quota used up

# --- Gemini generateContent (research R5) ---
GEMINI_API_PATH: Final = "/v1beta/models"
GEMINI_METHOD: Final = "generateContent"
GEMINI_THINKING_LEVEL: Final = "LOW"  # same intent as LLM_EFFORT for Anthropic
GEMINI_JSON_MIME: Final = "APPLICATION_JSON"
