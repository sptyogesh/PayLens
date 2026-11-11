"""Read-only FIRA queries shared by the FIRA page, the upload result and the chat tool (004).

A payment's FIRA status is read from transactions.fira_status (written by the rematch); an
eligible payment without a matched or needs-review FIRA counts as missing, so every screen agrees.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.dates import ist_date
from app.common.types import FiraStatus
from app.models import FiraDocStatus, FiraDocument, FiraMatch, Transaction
from app.schemas.common import MoneyOut
from app.schemas.fira import FiraItemOut, FiraMatchOut, FiraPaymentOut, FiraSummaryOut
from app.services.leakage_query import eligible_in_range

LINKED = frozenset({FiraStatus.MATCHED, FiraStatus.NEEDS_REVIEW})


def payment_fira_status(row: Transaction) -> FiraStatus:
    return row.fira_status if row.fira_status in LINKED else FiraStatus.MISSING


def missing_payments(session: Session) -> list[Transaction]:
    """Eligible payments (all time, newest first) with no matched or needs-review FIRA."""
    rows = session.scalars(eligible_in_range(None, None))
    return [row for row in rows if payment_fira_status(row) is FiraStatus.MISSING]


def summary(session: Session) -> FiraSummaryOut:
    query = select(FiraDocument.status, func.count()).group_by(FiraDocument.status)
    counts = {status: int(count) for status, count in session.execute(query)}
    return FiraSummaryOut(
        matched=counts.get(FiraDocStatus.MATCHED, 0),
        needs_review=counts.get(FiraDocStatus.NEEDS_REVIEW, 0),
        no_match=counts.get(FiraDocStatus.NO_MATCH, 0),
        missing_payments=len(missing_payments(session)),
    )


def payment_out(row: Transaction) -> FiraPaymentOut:
    return FiraPaymentOut(
        transaction_id=row.id,
        paypal_transaction_id=row.paypal_transaction_id,
        date=ist_date(row.occurred_at),
        client=row.client.name,
        gross=MoneyOut.of(row.gross_amount, row.currency),
    )


def matches_by_fira(session: Session) -> dict[str, list[FiraMatchOut]]:
    query = (
        select(FiraMatch, Transaction.paypal_transaction_id)
        .join(Transaction, Transaction.id == FiraMatch.transaction_id)
        .order_by(Transaction.occurred_at, Transaction.paypal_transaction_id)
    )
    found: dict[str, list[FiraMatchOut]] = {}
    for match, paypal_id in session.execute(query):
        found.setdefault(str(match.fira_id), []).append(
            FiraMatchOut(
                transaction_id=match.transaction_id,
                paypal_transaction_id=paypal_id,
                score=match.match_score,
                kind=match.kind,
            )
        )
    return found


def fira_items(session: Session) -> list[FiraItemOut]:
    """Every FIRA, newest upload first, with the payments linked to it."""
    query = select(FiraDocument).order_by(FiraDocument.uploaded_at.desc(), FiraDocument.id)
    matches = matches_by_fira(session)
    return [
        FiraItemOut.from_model(doc, matches.get(str(doc.id), [])) for doc in session.scalars(query)
    ]
