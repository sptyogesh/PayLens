"""FIRA upload coordinator (004 FR-001, FR-002, FR-012): check → dedupe → extract → store → rematch.

Files are checked before any AI call (E6). The PDF bytes are never stored or logged: only the
SHA-256 hash, the sanitised file name and the extracted fields.
"""

import hashlib
import logging
import re
from collections.abc import Callable
from decimal import Decimal
from typing import Final

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.ai.fira_extract import ISO_CURRENCY, ExtractionOutcome, FiraExtractionError, extract
from app.ai.llm import LlmClient
from app.common.constants import (
    FIRA_AMOUNT_MAX,
    FIRA_FILE_NAME_MAX,
    FIRA_FILE_SUFFIX,
    FIRA_MAX_BYTES,
    FIRA_PDF_MEDIA_TYPE,
    FIRA_PDF_SIGNATURE,
    FIRA_PURPOSE_CODE_MAX,
    FIRA_RATE_MAX,
    FIRA_REASON_MAX,
    FIRA_REFERENCE_MAX,
    FIRA_REMITTER_MAX,
)
from app.common.dates import utc_now
from app.common.errors import LlmConfigError, LlmUnavailableError
from app.common.money import round_money, round_rate
from app.engine.fira_match import REASON_SEPARATOR
from app.models import FiraDocStatus, FiraDocument
from app.schemas.fira import FiraListOut, UploadFileOut, UploadOutcome, UploadResultOut
from app.services.fira_query import fira_items, missing_payments, payment_out, summary
from app.services.fira_rematch import safe_rematch

logger = logging.getLogger(__name__)

SessionFactory = Callable[[], Session]
UNSAFE_NAME_CHARS: Final = re.compile(r"[\x00-\x1f\x7f]")
NOT_PDF: Final = "Only PDF files can be uploaded."
NOT_PDF_NAME: Final = "The file name must end with .pdf."
EMPTY: Final = "The file is empty."
TOO_LARGE: Final = f"The file is larger than {FIRA_MAX_BYTES // (1024 * 1024)} MB."
DUPLICATE: Final = "This FIRA was already uploaded."
UNREADABLE: Final = "We could not read this FIRA, so nothing was saved. Please check the file."
AI_DOWN: Final = "The AI reader is not available right now, so nothing was saved. Try again later."
MATCH_PENDING: Final = (
    "Saved. Matching could not run now; it will run again after the next upload or sync."
)
STORED: Final = {
    FiraDocStatus.MATCHED: "Read and matched to a payment.",
    FiraDocStatus.NEEDS_REVIEW: "Read, but it needs review.",
    FiraDocStatus.NO_MATCH: "Read, but no matching payment was found.",
}


def sanitise_name(file_name: str) -> str:
    """Base name only, no control characters, at most FIRA_FILE_NAME_MAX characters."""
    base = re.split(r"[\\/]", file_name)[-1]
    return UNSAFE_NAME_CHARS.sub("", base).strip()[-FIRA_FILE_NAME_MAX:]


def file_problem(name: str, content_type: str, body: bytes) -> str | None:
    """Why the file is rejected before any AI call (E6), or None when it may be read."""
    if not name.lower().endswith(FIRA_FILE_SUFFIX):
        return NOT_PDF_NAME
    if content_type.split(";", maxsplit=1)[0].strip().lower() != FIRA_PDF_MEDIA_TYPE:
        return NOT_PDF
    if not body:
        return EMPTY
    if len(body) > FIRA_MAX_BYTES:
        return TOO_LARGE
    return None if body.startswith(FIRA_PDF_SIGNATURE) else NOT_PDF


def fit_money(value: Decimal | None) -> Decimal | None:
    """Values that cannot be real (≤ 0 or too large) are not stored; the reason is kept."""
    return round_money(value) if value is not None and 0 < value <= FIRA_AMOUNT_MAX else None


def fit_text(value: str | None, limit: int) -> str | None:
    return value[:limit] if value else None


def new_document(name: str, file_hash: str, outcome: ExtractionOutcome) -> FiraDocument:
    """Every stored value fits its column, so a strange extraction is Needs review, not a 500."""
    fields = outcome.extraction
    problems = REASON_SEPARATOR.join(outcome.problems)[:FIRA_REASON_MAX] or None
    rate = fields.rate
    currency = fields.currency if fields.currency and ISO_CURRENCY.match(fields.currency) else None
    return FiraDocument(
        file_name=name,
        file_hash=file_hash,
        extracted_json=fields.model_dump(mode="json"),
        foreign_amount=fit_money(fields.foreign_amount),
        currency=currency,
        inr_amount=fit_money(fields.inr_amount),
        rate=round_rate(rate) if rate is not None and 0 < rate <= FIRA_RATE_MAX else None,
        remittance_date=fields.remittance_date,
        reference_no=fit_text(fields.reference_no, FIRA_REFERENCE_MAX),
        remitter=fit_text(fields.remitter, FIRA_REMITTER_MAX),
        purpose_code=fit_text(fields.purpose_code, FIRA_PURPOSE_CODE_MAX),
        status=FiraDocStatus.NEEDS_REVIEW if problems else FiraDocStatus.NO_MATCH,
        reason=problems,
        validation_reason=problems,
        uploaded_at=utc_now(),
    )


def is_duplicate(factory: SessionFactory, file_hash: str) -> bool:
    with factory() as session:
        found = session.scalar(select(FiraDocument.id).where(FiraDocument.file_hash == file_hash))
        return found is not None


def store(factory: SessionFactory, document: FiraDocument) -> bool:
    """Insert and commit; False only when the same hash was stored meanwhile (F14).
    Any other integrity error is a bug and is raised (never reported as a duplicate)."""
    with factory() as session:
        session.add(document)
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            if is_duplicate(factory, document.file_hash):
                return False
            raise
        return True


def finish(factory: SessionFactory, file: UploadFileOut) -> UploadResultOut:
    with factory() as session:
        if file.fira_id is not None and file.message != MATCH_PENDING:
            doc = session.get(FiraDocument, file.fira_id)
            if doc is not None:
                file = file.model_copy(update={"status": doc.status, "message": STORED[doc.status]})
        return UploadResultOut(result=file, summary=summary(session))


def outcome_of(name: str, outcome: UploadOutcome, message: str) -> UploadFileOut:
    return UploadFileOut(
        file_name=name, outcome=outcome, message=message, fira_id=None, status=None
    )


def read_and_store(
    factory: SessionFactory, llm: LlmClient, name: str, body: bytes
) -> UploadFileOut:
    file_hash = hashlib.sha256(body).hexdigest()
    if is_duplicate(factory, file_hash):
        return outcome_of(name, "duplicate", DUPLICATE)
    try:
        extracted = extract(llm, body, name)
    except FiraExtractionError:
        return outcome_of(name, "failed", UNREADABLE)
    except (LlmUnavailableError, LlmConfigError) as error:
        logger.warning("FIRA extraction skipped: %s", error.code)
        return outcome_of(name, "failed", AI_DOWN)
    document = new_document(name, file_hash, extracted)
    if not store(factory, document):
        return outcome_of(name, "duplicate", DUPLICATE)
    if safe_rematch(factory) is None:  # saved, but the statuses could not be recomputed
        pending = outcome_of(name, "stored", MATCH_PENDING)
        return pending.model_copy(update={"fira_id": document.id})
    stored = outcome_of(name, "stored", STORED[document.status])
    return stored.model_copy(update={"fira_id": document.id, "status": document.status})


def upload(
    factory: SessionFactory,
    llm: LlmClient,
    file_name: str,
    body: bytes,
    content_type: str = FIRA_PDF_MEDIA_TYPE,
) -> UploadResultOut:
    """One file. Problems are outcomes (rejected / duplicate / failed), never exceptions."""
    name = sanitise_name(file_name)
    problem = file_problem(name, content_type, body)
    if problem is not None:
        return finish(factory, outcome_of(name, "rejected", problem))
    return finish(factory, read_and_store(factory, llm, name, body))


def list_firas(session: Session) -> FiraListOut:
    return FiraListOut(
        summary=summary(session),
        items=fira_items(session),
        missing=[payment_out(row) for row in missing_payments(session)],
    )
