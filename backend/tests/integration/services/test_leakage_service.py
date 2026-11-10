"""Recalculation fills, retries and clears leakage columns (FR-010 to FR-021)."""

from decimal import Decimal

from freezegun import freeze_time
from sqlalchemy.orm import Session, sessionmaker

from app.common.types import TransactionKind, TransactionStatus
from app.fakes.fx_fake import FakeFxGateway
from app.services.leakage_service import recalculate_leakage, safe_recalculate
from tests.fixtures.rows import add_client, add_tx

D = Decimal


@freeze_time("2026-11-10 06:00:00")
def test_completed_income_gets_section_10_values(db_session: Session) -> None:
    row = add_tx(db_session, add_client(db_session), "TX1")
    summary = recalculate_leakage(db_session, FakeFxGateway())
    assert summary.calculated == 1
    assert (row.mid_market_rate, row.paypal_rate) == (D("84.000000"), D("81.480000"))
    assert row.inr_received == D("77894.88")  # 956 x 81.48
    assert row.fee_loss_inr == D("3696.00")
    assert row.fx_loss_inr == D("2409.12")  # 956 x 2.52
    assert row.total_leakage_inr == D("6105.12")


@freeze_time("2026-11-10 06:00:00")
def test_p8_non_income_and_pending_get_no_leakage(db_session: Session) -> None:
    client = add_client(db_session)
    withdrawal = add_tx(db_session, client, "W1", kind=TransactionKind.WITHDRAWAL)
    pending = add_tx(db_session, client, "P1", status=TransactionStatus.PENDING)
    pending.total_leakage_inr = D("1.00")  # stale value from before the status changed
    recalculate_leakage(db_session, FakeFxGateway())
    assert withdrawal.total_leakage_inr is None
    assert pending.total_leakage_inr is None


@freeze_time("2026-11-10 06:00:00")
def test_missing_rate_leaves_row_empty_and_is_retried(db_session: Session) -> None:
    row = add_tx(db_session, add_client(db_session), "TX1")
    summary = recalculate_leakage(db_session, FakeFxGateway(unavailable=True))
    assert (summary.rate_unavailable, row.total_leakage_inr) == (1, None)
    recalculate_leakage(db_session, FakeFxGateway())
    assert row.total_leakage_inr == D("6105.12")


@freeze_time("2026-11-10 06:00:00")
def test_fee_greater_than_gross_is_not_calculated(db_session: Session) -> None:
    row = add_tx(db_session, add_client(db_session), "TX1", gross="1.00", fee="2.00")
    assert recalculate_leakage(db_session, FakeFxGateway()).invalid == 1
    assert row.total_leakage_inr is None


@freeze_time("2026-11-10 06:00:00")
def test_inr_payment_has_zero_fx_loss(db_session: Session) -> None:
    row = add_tx(db_session, add_client(db_session, "Ravi", "INR"), "TX1", gross="500", fee="20")
    recalculate_leakage(db_session, FakeFxGateway())
    assert (row.fx_loss_inr, row.fee_loss_inr, row.inr_received) == (
        D("0.00"),
        D("20.00"),
        D("480.00"),
    )


def test_safe_recalculate_never_raises(session_factory: sessionmaker[Session]) -> None:
    def broken_factory() -> Session:
        raise RuntimeError("database down")

    assert safe_recalculate(broken_factory, FakeFxGateway()) is None
    assert safe_recalculate(session_factory, FakeFxGateway()) is not None
