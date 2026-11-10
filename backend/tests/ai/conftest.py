import pytest
from sqlalchemy.orm import Session

from tests.ai.support import seed_payments


@pytest.fixture
def seeded(db_session: Session) -> Session:
    """Nine payments, three clients (USD, GBP, EUR), Feb-Nov 2026, leakage calculated."""
    return seed_payments(db_session)
