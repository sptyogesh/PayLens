"""Global FIRA rematch (004 FR-004 to FR-007): engine results → tables and transactions.fira_status.

Demo scale: every valid FIRA against every eligible payment, recomputed after each upload, sync,
seed and /pay. FIRAs that failed code validation stay needs review with their own reason.
"""

import logging
import uuid
from collections.abc import Callable
from typing import Final

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.common.constants import FIRA_REMATCH_LOCK_KEY
from app.common.dates import ist_date
from app.common.types import FiraStatus
from app.engine.fira_match import FiraCandidate, FiraOutcome, MatchResult, PaymentCandidate
from app.engine.fira_match import match_all as engine_match_all
from app.engine.leakage import is_eligible
from app.models import FiraDocStatus, FiraDocument, FiraMatch, FiraMatchKind, Transaction

logger = logging.getLogger(__name__)

NO_SCORE: Final = 0


def is_valid(doc: FiraDocument) -> bool:
    """Matchable: amount, currency and date present and no validation problem."""
    has_fields = None not in (doc.foreign_amount, doc.currency, doc.remittance_date)
    return has_fields and doc.validation_reason is None


def fira_candidates(docs: list[FiraDocument]) -> list[FiraCandidate]:
    return [
        FiraCandidate(
            fira_key=str(doc.id),
            amount=doc.foreign_amount,
            currency=doc.currency,
            date=doc.remittance_date,
            reference=doc.reference_no,
            order=order,
        )
        for order, doc in enumerate(docs)
        if doc.foreign_amount is not None
        and doc.currency is not None
        and doc.remittance_date is not None
    ]


def payment_candidates(rows: list[Transaction]) -> list[PaymentCandidate]:
    return [
        PaymentCandidate(
            payment_key=str(row.id),
            paypal_transaction_id=row.paypal_transaction_id,
            gross=row.gross_amount,
            currency=row.currency,
            date=ist_date(row.occurred_at),
        )
        for row in rows
        if row.gross_amount > 0
    ]


def store_outcome(session: Session, doc: FiraDocument, outcome: FiraOutcome) -> None:
    doc.status, doc.score, doc.reason = FiraDocStatus(outcome.status), outcome.score, outcome.reason
    if outcome.kind is None:
        return
    for payment_key in outcome.payment_keys:
        session.add(
            FiraMatch(
                fira_id=doc.id,
                transaction_id=uuid.UUID(payment_key),
                match_score=outcome.score or NO_SCORE,
                kind=FiraMatchKind(outcome.kind),
            )
        )


def store_payment_statuses(rows: list[Transaction], result: MatchResult) -> None:
    for row in rows:
        new = None
        if is_eligible(row.kind, row.status):
            new = FiraStatus(result.payments.get(str(row.id), FiraStatus.MISSING))
        if row.fira_status != new:
            row.fira_status = new


def rematch(session: Session) -> MatchResult:
    """Recompute every FIRA status, all links and every payment's FIRA status. Flushes only."""
    # One rematch at a time (upload, sync and /pay can overlap); released at commit/rollback.
    session.execute(select(func.pg_advisory_xact_lock(FIRA_REMATCH_LOCK_KEY)))
    docs = list(
        session.scalars(select(FiraDocument).order_by(FiraDocument.uploaded_at, FiraDocument.id))
    )
    valid = [doc for doc in docs if is_valid(doc)]
    rows = list(session.scalars(select(Transaction)))
    eligible = [row for row in rows if is_eligible(row.kind, row.status)]
    result = engine_match_all(fira_candidates(valid), payment_candidates(eligible))
    session.execute(delete(FiraMatch))
    outcomes = {outcome.fira_key: outcome for outcome in result.firas}
    for doc in docs:
        if doc.validation_reason is not None or str(doc.id) not in outcomes:
            doc.status, doc.score = FiraDocStatus.NEEDS_REVIEW, None
            doc.reason = doc.validation_reason
        else:
            store_outcome(session, doc, outcomes[str(doc.id)])
    store_payment_statuses(rows, result)
    session.flush()
    return result


def safe_rematch(factory: Callable[[], Session]) -> MatchResult | None:
    """Never fails the caller (upload, sync, seed, /pay): errors are logged, statuses wait."""
    try:
        with factory() as session:
            result = rematch(session)
            session.commit()
            return result
    except Exception:
        logger.exception("FIRA rematch failed")
        return None


def delete_all_firas(session: Session) -> int:
    """Demo reset only (`seed_demo --reset`): remove every FIRA; matches go with them (cascade)."""
    session.execute(delete(FiraMatch))
    removed = session.execute(delete(FiraDocument))
    return int(getattr(removed, "rowcount", 0))
