"""Typed settings loaded from the environment (FR-006). Missing values fail at startup."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.common.constants import FX_API_DEFAULT_URL, PAYPAL_SANDBOX_BASE_URL


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    paypal_mode: Literal["http", "fake"] = "http"
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_base_url: str = PAYPAL_SANDBOX_BASE_URL
    database_url: str = Field(min_length=1)
    frontend_url: str = ""
    trust_proxy_headers: bool = False
    startup_sync_enabled: bool = True
    rate_limit_enabled: bool = True
    fx_mode: Literal["http", "fake"] = "http"
    fx_api_url: str = FX_API_DEFAULT_URL

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
