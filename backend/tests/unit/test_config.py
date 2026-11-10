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
