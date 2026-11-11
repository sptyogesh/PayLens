"""Fill the leakage columns of every transaction (FR-010 to FR-021, research R6).

Demo scale makes "recalculate everything" cheap and always correct; cached rates are reused.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.dates import ist_date
from app.engine.leakage import (
    LeakageInput,
    LeakageResult,
    calculate_leakage,
    is_eligible,
    paypal_rate_for,
)
from app.fx import FxGateway
from app.models import Transaction
from app.services.fx_rate_service import RateLookup

logger = logging.getLogger(__name__)


@dataclass
class RecalcSummary:
    calculated: int = 0
    rate_unavailable: int = 0
    invalid: int = 0


def store_leakage(row: Transaction, data: LeakageInput, result: LeakageResult) -> None:
    row.mid_market_rate, row.paypal_rate = data.mid_rate, data.paypal_rate
    row.inr_received, row.fee_loss_inr = result.inr_received, result.fee_loss_inr
    row.fx_loss_inr, row.total_leakage_inr = result.fx_loss_inr, result.total_leakage_inr


def apply_leakage(row: Transaction, rates: RateLookup, summary: RecalcSummary) -> None:
    mid = rates.mid_rate(row.currency, ist_date(row.occurred_at))
    paypal = paypal_rate_for(row.currency, mid) if mid is not None else None
    row.clear_leakage()
    try:
        data = LeakageInput(
            gross=row.gross_amount,
            fee=row.fee_amount,
            currency=row.currency,
            mid_rate=mid,
            paypal_rate=paypal,
        )
    except ValidationError:
        summary.invalid += 1
        return
    result = calculate_leakage(data)
    if isinstance(result, LeakageResult):
        store_leakage(row, data, result)
        summary.calculated += 1
    else:
        summary.rate_unavailable += 1


def recalculate_leakage(session: Session, fx: FxGateway) -> RecalcSummary:
    rates, summary = RateLookup(session, fx), RecalcSummary()
    for row in session.scalars(select(Transaction)):
        if is_eligible(row.kind, row.status):
            apply_leakage(row, rates, summary)
        elif row.total_leakage_inr is not None or row.mid_market_rate is not None:
            row.clear_leakage()
    session.flush()
    return summary


def safe_recalculate(factory: Callable[[], Session], fx: FxGateway) -> RecalcSummary | None:
    """Never fails the caller (sync, seed, /pay): errors are logged and leakage waits (FR-005)."""
    try:
        with factory() as session:
            summary = recalculate_leakage(session, fx)
            session.commit()
            return summary
    except Exception:
        logger.exception("Leakage recalculation failed")
        return None
