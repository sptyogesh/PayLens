"""Typed settings loaded from the environment (FR-006). Missing values fail at startup."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.common.constants import FX_API_DEFAULT_URL, LOCAL_PROXY, PAYPAL_SANDBOX_BASE_URL
from app.common.llm_provider import choose_llm


class Settings(BaseSettings):
    # Startup errors never echo the input values (they include LLM_API_KEY and PayPal secrets).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", hide_input_in_errors=True)

    app_env: Literal["development", "test", "production"] = "development"
    paypal_mode: Literal["http", "fake"] = "http"
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_base_url: str = PAYPAL_SANDBOX_BASE_URL
    database_url: str = Field(min_length=1)
    frontend_url: str = ""
    # Proxies allowed to set X-Forwarded-For (uvicorn format: IPs/CIDRs, comma-separated).
    forwarded_allow_ips: str = LOCAL_PROXY
    startup_sync_enabled: bool = True
    # Load the labelled demo seed in the startup thread (for hosts without a shell). Idempotent.
    seed_demo_on_startup: bool = False
    rate_limit_enabled: bool = True
    fx_mode: Literal["http", "fake"] = "http"
    fx_api_url: str = FX_API_DEFAULT_URL
    llm_mode: Literal["http", "fake"] = "http"
    # Empty provider: detected from the key prefix. Empty model / URL: the provider's default.
    llm_provider: Literal["", "anthropic", "gemini"] = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_api_url: str = ""

    @field_validator("llm_api_key")
    @classmethod
    def strip_key(cls, value: str) -> str:
        return value.strip()  # a pasted space or newline must not hide the key prefix

    @model_validator(mode="after")
    def check_safety_rules(self) -> "Settings":
        if self.paypal_mode == "fake" and self.app_env != "test":
            raise ValueError("PAYPAL_MODE=fake is only allowed when APP_ENV=test")
        if not self.rate_limit_enabled and self.app_env != "test":
            raise ValueError("RATE_LIMIT_ENABLED=false is only allowed when APP_ENV=test")
        if self.paypal_base_url.rstrip("/") != PAYPAL_SANDBOX_BASE_URL:
            raise ValueError(f"PAYPAL_BASE_URL must be the sandbox URL {PAYPAL_SANDBOX_BASE_URL}")
        if self.paypal_mode == "http" and not (self.paypal_client_id and self.paypal_client_secret):
            raise ValueError("PAYPAL_CLIENT_ID and PAYPAL_CLIENT_SECRET are required")
        if self.fx_mode == "fake" and self.app_env != "test":
            raise ValueError("FX_MODE=fake is only allowed when APP_ENV=test")
        if self.llm_mode == "fake" and self.app_env != "test":
            raise ValueError("LLM_MODE=fake is only allowed when APP_ENV=test")
        if self.llm_mode == "http" and not self.llm_api_key:
            raise ValueError("LLM_API_KEY is required (or LLM_MODE=fake with APP_ENV=test)")
        llm = choose_llm(self.llm_provider, self.llm_api_key, self.llm_model, self.llm_api_url)
        self.llm_provider, self.llm_model, self.llm_api_url = llm.provider, llm.model, llm.api_url
        return self

    @property
    def sqlalchemy_url(self) -> str:
        """Render gives postgres:// URLs; SQLAlchemy with psycopg 3 needs postgresql+psycopg://."""
        for prefix in ("postgres://", "postgresql://"):
            if self.database_url.startswith(prefix):
                return "postgresql+psycopg://" + self.database_url.removeprefix(prefix)
        return self.database_url


@lru_cache
def get_settings() -> Settings:
    return Settings()  # values come from the environment
