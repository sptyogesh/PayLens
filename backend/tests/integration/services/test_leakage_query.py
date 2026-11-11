"""003 T003: collect() returns the eligible rows of any half-open range, as the dashboard counts."""

from datetime import UTC, datetime
from decimal import Decimal

from freezegun import freeze_time
from sqlalchemy.orm import Session

from app.common.types import Money, TransactionKind, TransactionSource, TransactionStatus
from app.engine.leakage import totals
from app.fakes.fx_fake import FakeFxGateway
from app.services.leakage_query import collect
from app.services.leakage_service import recalculate_leakage
from tests.fixtures.rows import add_client, add_tx

NOW = "2026-11-10 06:00:00"
OCT_1_IST = datetime(2026, 9, 30, 18, 30, tzinfo=UTC)
NOV, SEP = datetime(2026, 11, 6, 6, 30, tzinfo=UTC), datetime(2026, 9, 6, 6, 30, tzinfo=UTC)


def seed(session: Session) -> None:
    ava, ben = add_client(session), add_client(session, "Ben Lee", "GBP")
    add_tx(session, ava, "NOV", occurred_at=NOV)
    add_tx(session, ben, "SEP", occurred_at=SEP, gross="200.00", fee="9.00")
    add_tx(session, ava, "EDGE", occurred_at=OCT_1_IST, source=TransactionSource.DEMO_SEED)
    add_tx(session, ava, "WD", occurred_at=NOV, kind=TransactionKind.WITHDRAWAL)
    add_tx(session, ava, "PEND", occurred_at=NOV, status=TransactionStatus.PENDING)
    add_tx(session, ava, "ODD", occurred_at=NOV, gross="1.00", fee="2.00")  # fee > gross
    recalculate_leakage(session, FakeFxGateway())


@freeze_time(NOW)
def test_all_eligible_rows_newest_first(db_session: Session) -> None:
    seed(db_session)
    data = collect(db_session, None, None)
    ids = [t.paypal_transaction_id for t in data.transactions]
    assert set(ids) == {"NOV", "ODD", "EDGE", "SEP"}
    assert ids[-2:] == ["EDGE", "SEP"]
    assert [i.transaction.paypal_transaction_id for i in data.items][-2:] == ["EDGE", "SEP"]
    assert (data.excluded_count, data.not_calculated_count) == (0, 1)
    assert data.sources == [TransactionSource.DEMO_SEED, TransactionSource.PAYPAL_SANDBOX]


@freeze_time(NOW)
def test_range_is_half_open(db_session: Session) -> None:
    seed(db_session)
    before = collect(db_session, None, OCT_1_IST)
    after = collect(db_session, OCT_1_IST, None)
    assert [r.month for r in before.rows] == ["2026-09"]
    assert {i.transaction.paypal_transaction_id for i in after.items} == {"NOV", "EDGE"}


@freeze_time(NOW)
def test_rows_carry_ist_month_client_and_gross(db_session: Session) -> None:
    seed(db_session)
    row = collect(db_session, None, OCT_1_IST).rows[0]
    assert (row.month, row.client_label) == ("2026-09", "Ben Lee")
    assert row.gross == Money(amount=Decimal("200.00"), currency="GBP")
    assert row.result.ideal_inr == Decimal("21300.00")


@freeze_time(NOW)
def test_rate_unavailable_is_counted_not_included(db_session: Session) -> None:
    add_tx(db_session, add_client(db_session), "NOV", occurred_at=NOV)
    recalculate_leakage(db_session, FakeFxGateway(unavailable=True))
    data = collect(db_session, None, None)
    assert (len(data.transactions), data.rows, data.excluded_count) == (1, [], 1)
    assert data.sources == []
    assert totals(data.rows).payment_count == 0
