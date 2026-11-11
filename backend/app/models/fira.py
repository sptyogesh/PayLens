"""fira_documents and fira_matches tables (004 data-model.md).

The uploaded PDF itself is never stored (FR-012): only its hash, name and extracted fields.
Matches are recomputed (delete + insert) on every rematch.
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import CHAR, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.common.constants import (
    FIRA_FILE_NAME_MAX,
    FIRA_PURPOSE_CODE_MAX,
    FIRA_REASON_MAX,
    FIRA_REFERENCE_MAX,
    FIRA_REMITTER_MAX,
)
from app.models.base import RATE, Base, IdMixin, TimestampMixin, pg_enum

SHA256_HEX_LENGTH = 64


class FiraDocStatus(StrEnum):
    MATCHED = "matched"
    NEEDS_REVIEW = "needs_review"
    NO_MATCH = "no_match"


class FiraMatchKind(StrEnum):
    DIRECT = "direct"
    WEEKLY = "weekly"


class FiraDocument(IdMixin, TimestampMixin, Base):
    __tablename__ = "fira_documents"
    __table_args__ = (
        CheckConstraint("foreign_amount > 0", name="ck_fira_documents_amount_positive"),
        CheckConstraint("score BETWEEN 0 AND 100", name="ck_fira_documents_score_range"),
    )

    file_name: Mapped[str] = mapped_column(String(FIRA_FILE_NAME_MAX))
    file_hash: Mapped[str] = mapped_column(CHAR(SHA256_HEX_LENGTH), unique=True)
    extracted_json: Mapped[dict[str, Any]] = mapped_column(JSONB)
    foreign_amount: Mapped[Decimal | None]
    currency: Mapped[str | None] = mapped_column(CHAR(3))
    inr_amount: Mapped[Decimal | None]
    rate: Mapped[Decimal | None] = mapped_column(RATE)
    remittance_date: Mapped[date | None]
    reference_no: Mapped[str | None] = mapped_column(String(FIRA_REFERENCE_MAX))
    remitter: Mapped[str | None] = mapped_column(String(FIRA_REMITTER_MAX))  # data only
    purpose_code: Mapped[str | None] = mapped_column(String(FIRA_PURPOSE_CODE_MAX))
    status: Mapped[FiraDocStatus] = mapped_column(pg_enum(FiraDocStatus, "fira_doc_status"))
    score: Mapped[int | None]
    reason: Mapped[str | None] = mapped_column(String(FIRA_REASON_MAX))
    # Why code validation failed (E2/E3); such a FIRA stays needs review and is never matched.
    validation_reason: Mapped[str | None] = mapped_column(String(FIRA_REASON_MAX))
    # Set by the app (not now()) so uploads in one DB transaction keep their order (F11 ties).
    uploaded_at: Mapped[datetime]


class FiraMatch(IdMixin, Base):
    """One payment linked to one FIRA. A payment is linked to at most one FIRA (FR-005)."""

    __tablename__ = "fira_matches"
    __table_args__ = (
        UniqueConstraint("transaction_id", name="uq_fira_matches_transaction"),
        CheckConstraint("match_score BETWEEN 0 AND 100", name="ck_fira_matches_score_range"),
    )

    fira_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("fira_documents.id", ondelete="CASCADE"), index=True
    )
    transaction_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("transactions.id", ondelete="CASCADE")
    )
    match_score: Mapped[int]
    kind: Mapped[FiraMatchKind] = mapped_column(pg_enum(FiraMatchKind, "fira_match_kind"))
