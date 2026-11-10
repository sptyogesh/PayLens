"""transactions table (data-model.md).

Holds the empty 002/004 columns now so later features need no schema change.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CHAR, CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.types import (
    FiraStatus,
    TransactionKind,
    TransactionOrigin,
    TransactionSource,
    TransactionStatus,
)
from app.models.base import RATE, Base, IdMixin, TimestampMixin, pg_enum
from app.models.client import Client


class Transaction(IdMixin, TimestampMixin, Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("fee_amount >= 0", name="ck_transactions_fee_non_negative"),
        CheckConstraint("gross_amount >= 0", name="ck_transactions_gross_non_negative"),
        CheckConstraint("net_amount = gross_amount - fee_amount", name="ck_transactions_net"),
        Index(
            "ix_transactions_occurred_at_desc",
            "occurred_at",
            postgresql_ops={"occurred_at": "DESC"},
        ),
    )

    paypal_transaction_id: Mapped[str] = mapped_column(String(32), unique=True)
    paypal_order_id: Mapped[str | None] = mapped_column(String(32))
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"), index=True)
    occurred_at: Mapped[datetime]
    event_code: Mapped[str | None] = mapped_column(String(8))
    kind: Mapped[TransactionKind] = mapped_column(
        pg_enum(TransactionKind, "transaction_kind"), index=True
    )
    status: Mapped[TransactionStatus] = mapped_column(
        pg_enum(TransactionStatus, "transaction_status")
    )
    gross_amount: Mapped[Decimal]
    fee_amount: Mapped[Decimal]
    net_amount: Mapped[Decimal]
    currency: Mapped[str] = mapped_column(CHAR(3))
    source: Mapped[TransactionSource] = mapped_column(
        pg_enum(TransactionSource, "transaction_source"), index=True
    )
    origin: Mapped[TransactionOrigin] = mapped_column(
        pg_enum(TransactionOrigin, "transaction_origin")
    )
    is_flagged: Mapped[bool] = mapped_column(default=False)
    flag_reason: Mapped[str | None] = mapped_column(String(200))
    raw_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    # Filled by 002-leakage-dashboard and 004-fira-matching. Never written by 001.
    mid_market_rate: Mapped[Decimal | None] = mapped_column(RATE)
    paypal_rate: Mapped[Decimal | None] = mapped_column(RATE)
    inr_received: Mapped[Decimal | None]
    fee_loss_inr: Mapped[Decimal | None]
    fx_loss_inr: Mapped[Decimal | None]
    total_leakage_inr: Mapped[Decimal | None]
    fira_status: Mapped[FiraStatus | None] = mapped_column(pg_enum(FiraStatus, "fira_status"))

    client: Mapped[Client] = relationship(lazy="joined")

    def leakage_inputs(self) -> tuple[object, ...]:
        """The fields leakage depends on; when any of them changes, leakage is stale."""
        return (
            self.kind,
            self.status,
            self.gross_amount,
            self.fee_amount,
            self.currency,
            self.occurred_at,
        )

    def clear_leakage(self) -> None:
        """Remove calculated leakage; the next recalculation fills it again (002 FR-020)."""
        self.mid_market_rate = self.paypal_rate = None
        self.inr_received = self.fee_loss_inr = None
        self.fx_loss_inr = self.total_leakage_inr = None
