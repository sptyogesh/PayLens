from decimal import Decimal

from app.common.types import (
    TransactionKind,
    TransactionOrigin,
    TransactionSource,
    TransactionStatus,
)
from app.models import Transaction
from app.schemas.leakage import leakage_out, leakage_status

D = Decimal


def row(**overrides: object) -> Transaction:
    values: dict[str, object] = {
        "kind": TransactionKind.INCOME,
        "status": TransactionStatus.COMPLETED,
        "gross_amount": D("1000.00"),
        "fee_amount": D("44.00"),
        "net_amount": D("956.00"),
        "currency": "USD",
        "source": TransactionSource.DEMO_SEED,
        "origin": TransactionOrigin.SEED,
    }
    values.update(overrides)
    return Transaction(**values)


def test_l1_worked_example_through_the_api_schema() -> None:
    out = leakage_out(
        row(
            mid_market_rate=D("84.000000"),
            paypal_rate=D("81.500000"),
            inr_received=D("77914.00"),
            fee_loss_inr=D("3696.00"),
            fx_loss_inr=D("2390.00"),
            total_leakage_inr=D("6086.00"),
        )
    )
    assert out is not None
    assert (out.ideal_inr.amount, out.total_leakage_inr.amount) == ("84000.00", "6086.00")
    assert (out.leakage_percent, out.paypal_rate) == ("7.25", "81.500000")


def test_status_for_each_case() -> None:
    assert leakage_status(row(total_leakage_inr=D("1.00"))) == "calculated"
    assert leakage_status(row()) == "rate_unavailable"
    assert leakage_status(row(fee_amount=D("2000.00"))) == "not_calculated"
    assert leakage_status(row(kind=TransactionKind.REFUND)) == "not_applicable"
    assert leakage_out(row()) is None
