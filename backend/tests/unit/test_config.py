import pytest
from pydantic import ValidationError

from app.config import Settings

DB = "postgresql://u:p@h/db"


def test_fake_paypal_is_refused_outside_test_env() -> None:
    with pytest.raises(ValidationError, match="only allowed when APP_ENV=test"):
        Settings(app_env="production", paypal_mode="fake", database_url=DB)


def test_only_sandbox_base_url_is_allowed() -> None:
    with pytest.raises(ValidationError, match="sandbox"):
        Settings(
            app_env="test",
            paypal_mode="fake",
            paypal_base_url="https://api-m.paypal.com",
            database_url=DB,
        )


def test_http_mode_requires_credentials() -> None:
    with pytest.raises(ValidationError, match="PAYPAL_CLIENT_ID"):
        Settings(app_env="development", paypal_mode="http", database_url=DB)


def test_missing_database_url_names_the_setting(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValidationError, match="database_url"):
        Settings(_env_file=None)


@pytest.mark.parametrize(
    "url", ["postgres://u:p@h/db", "postgresql://u:p@h/db", "postgresql+psycopg://u:p@h/db"]
)
def test_render_urls_are_normalised_for_psycopg(url: str) -> None:
    settings = Settings(app_env="test", paypal_mode="fake", database_url=url)
    assert settings.sqlalchemy_url == "postgresql+psycopg://u:p@h/db"


def test_rate_limits_cannot_be_disabled_outside_test_env() -> None:
    with pytest.raises(ValidationError, match="RATE_LIMIT_ENABLED"):
        Settings(
            app_env="development",
            paypal_mode="http",
            paypal_client_id="id",
            paypal_client_secret="secret",
            rate_limit_enabled=False,
            database_url=DB,
        )


def test_fake_fx_is_refused_outside_test_env() -> None:
    with pytest.raises(ValidationError, match="FX_MODE=fake"):
        Settings(
            app_env="production",
            paypal_mode="http",
            fx_mode="fake",
            paypal_client_id="id",
            paypal_client_secret="secret",
            database_url=DB,
        )


def test_fx_defaults_to_frankfurter() -> None:
    settings = Settings(app_env="test", paypal_mode="fake", database_url=DB)
    assert settings.fx_api_url == "https://api.frankfurter.dev"


def test_fake_llm_is_refused_outside_test_env() -> None:
    with pytest.raises(ValidationError, match="LLM_MODE=fake"):
        Settings(
            app_env="production",
            paypal_mode="http",
            fx_mode="http",
            llm_mode="fake",
            paypal_client_id="id",
            paypal_client_secret="secret",
            database_url=DB,
        )


def test_http_llm_requires_a_key() -> None:
    with pytest.raises(ValidationError, match="LLM_API_KEY"):
        Settings(
            app_env="test", paypal_mode="fake", fx_mode="fake", llm_mode="http", database_url=DB
        )
