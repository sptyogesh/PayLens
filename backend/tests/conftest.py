"""Shared pytest fixtures.

Unit tests need no database. Tests that use `db_session` need PostgreSQL via
TEST_DATABASE_URL and FAIL (never skip) when it is missing (research R11).
"""

import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def read_env_file_value(name: str) -> str:
    """Read one KEY=value from backend/.env (gitignored), for hooks run outside a shell."""
    if not ENV_FILE.is_file():
        return ""
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition("=")
        if key.strip() == name:
            return value.strip().strip('"')
    return ""


TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or read_env_file_value("TEST_DATABASE_URL")
MISSING_DB_MESSAGE = "Set TEST_DATABASE_URL to a PostgreSQL 18 database (see quickstart)."

# Test-mode settings for every test. Real PayPal is never reachable from tests.
os.environ["APP_ENV"] = "test"
os.environ["PAYPAL_MODE"] = "fake"
os.environ["STARTUP_SYNC_ENABLED"] = "false"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL or "postgresql+psycopg://localhost/missing"
os.environ["FRONTEND_URL"] = "http://frontend.test"

from app.api.deps import reset_limiters  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
def _fresh_state() -> Iterator[None]:
    get_settings.cache_clear()
    reset_limiters()
    yield
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def db_engine() -> Iterator[Engine]:
    if not TEST_DATABASE_URL:
        pytest.fail(MISSING_DB_MESSAGE, pytrace=False)
    engine = create_engine(get_settings().sqlalchemy_url)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine: Engine) -> Iterator[Session]:
    """A session inside a transaction that is rolled back after the test."""
    with db_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint")
        try:
            yield session
        finally:
            session.close()
            transaction.rollback()
