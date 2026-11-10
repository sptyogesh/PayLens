"""FR-040 to FR-042: idempotent demo seed and reset that never touches sandbox data."""

from datetime import UTC, datetime
from decimal import Decimal

from freezegun import freeze_time
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.types import TransactionOrigin, TransactionSource
from app.models import Client, Transaction
from app.paypal.mapper import from_search_row
from app.paypal.schemas import TransactionDetail
from app.paypal.upsert import upsert_transaction
from app.services.seed_service import count_seed_rows, months_before, reset_seed, seed_fee
from scripts.seed_demo import seed
from tests.fixtures.paypal.search import row


def seeded(session: Session) -> list[Transaction]:
    query = select(Transaction).where(Transaction.source == TransactionSource.DEMO_SEED)
    return list(session.scalars(query))


@freeze_time("2026-11-10 12:00:00")
def test_first_run_adds_24_rows_over_4_clients_and_months(db_session: Session) -> None:
    assert seed(db_session) == 24
    rows = seeded(db_session)
    assert len(rows) == 24
    assert len({r.client_id for r in rows}) == 4
    assert {(r.occurred_at.year, r.occurred_at.month) for r in rows} == {
        (2026, 10),
        (2026, 9),
        (2026, 8),
        (2026, 7),
    }
    assert {r.currency for r in rows} == {"USD", "GBP", "EUR", "AUD"}
    assert all(r.origin is TransactionOrigin.SEED for r in rows)
    assert all(r.net_amount == r.gross_amount - r.fee_amount and r.fee_amount > 0 for r in rows)


def test_second_run_adds_nothing(db_session: Session) -> None:
    seed(db_session)
    assert seed(db_session) == 0
    assert count_seed_rows(db_session) == 24


def test_seed_clients_are_fictional(db_session: Session) -> None:
    seed(db_session)
    clients = db_session.scalars(select(Client).where(Client.source == TransactionSource.DEMO_SEED))
    assert all(c.email and c.email.endswith("@example.com") and "(demo)" in c.name for c in clients)


def test_reset_removes_only_demo_seed(db_session: Session) -> None:
    data = row("SANDBOX1")
    upsert_transaction(db_session, from_search_row(TransactionDetail.model_validate(data), data))
    seed(db_session)
    assert reset_seed(db_session) == (24, 4)
    remaining = list(db_session.scalars(select(Transaction)))
    assert [r.paypal_transaction_id for r in remaining] == ["SANDBOX1"]
    assert remaining[0].source is TransactionSource.PAYPAL_SANDBOX


def test_fee_and_month_helpers() -> None:
    assert seed_fee(Decimal("1000.00"), "USD") == Decimal("44.30")
    assert seed_fee(Decimal("275.00"), "GBP") == Decimal("12.30")
    january = datetime(2026, 1, 15, tzinfo=UTC)
    assert months_before(january, 1, 3) == datetime(2025, 12, 3, 12, tzinfo=UTC)
    assert months_before(january, 4, 28) == datetime(2025, 9, 28, 12, tzinfo=UTC)
