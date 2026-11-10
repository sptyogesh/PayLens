"""Link a Transaction Search row to an earlier /pay capture when the IDs differ (research R1).

PayPal does not document that the capture ID equals the Transaction Search ID. If no row
has the search ID, look for exactly one unreconciled /pay capture with the same gross,
currency and payer email within CHECKOUT_RECONCILE_WINDOW_HOURS. Never merge blindly.
"""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.constants import CHECKOUT_RECONCILE_WINDOW_HOURS
from app.common.types import TransactionKind, TransactionOrigin
from app.models import Client, Transaction
from app.paypal.dto import TransactionUpsert

AMBIGUOUS_RECONCILE = "AMBIGUOUS_RECONCILE"


def find_capture_candidates(session: Session, dto: TransactionUpsert) -> list[Transaction]:
    if dto.kind is not TransactionKind.INCOME or dto.payer.email is None:
        return []
    window = timedelta(hours=CHECKOUT_RECONCILE_WINDOW_HOURS)
    query = (
        select(Transaction)
        .join(Client, Transaction.client_id == Client.id)
        .where(
            Transaction.origin == TransactionOrigin.CHECKOUT_CAPTURE,
            Transaction.gross_amount == dto.gross,
            Transaction.currency == dto.currency,
            Client.email == dto.payer.email,
            Transaction.occurred_at.between(dto.occurred_at - window, dto.occurred_at + window),
        )
    )
    return list(session.scalars(query))


def reconcile(session: Session, dto: TransactionUpsert) -> tuple[Transaction | None, str | None]:
    """Return (row to re-key, None), (None, flag reason) when ambiguous, or (None, None)."""
    if dto.origin is not TransactionOrigin.TRANSACTION_SEARCH:
        return None, None
    candidates = find_capture_candidates(session, dto)
    if len(candidates) == 1:
        return candidates[0], None
    return None, AMBIGUOUS_RECONCILE if len(candidates) > 1 else None
