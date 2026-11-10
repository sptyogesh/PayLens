"""fx_rates constraints from 002 data-model.md (needs PostgreSQL)."""

from datetime import UTC, date, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import FxRate

FRIDAY, SATURDAY = date(2026, 11, 6), date(2026, 11, 7)


def make_rate(**overrides: object) -> FxRate:
    values: dict[str, object] = {
        "currency": "USD",
        "rate_date": SATURDAY,
        "published_date": FRIDAY,
        "rate": Decimal("93.920000"),
        "source": "frankfurter_ecb",
        "fetched_at": datetime(2026, 11, 10, tzinfo=UTC),
    }
    values.update(overrides)
    return FxRate(**values)


def test_valid_rate_is_stored_exactly(db_session: Session) -> None:
    db_session.add(make_rate(rate=Decimal("93.123456")))
    db_session.flush()
    stored = db_session.query(FxRate).one()
    assert stored.rate == Decimal("93.123456")


@pytest.mark.parametrize(
    "overrides",
    [{"rate": Decimal("0")}, {"published_date": date(2026, 11, 8)}],
)
def test_invalid_rates_are_rejected(db_session: Session, overrides: dict[str, object]) -> None:
    db_session.add(make_rate(**overrides))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_one_rate_per_currency_and_date(db_session: Session) -> None:
    db_session.add(make_rate())
    db_session.flush()
    db_session.add(make_rate(rate=Decimal("94.000000")))
    with pytest.raises(IntegrityError):
        db_session.flush()
