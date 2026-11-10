"""clients table (data-model.md)."""

from sqlalchemy import CHAR, Index, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.types import TransactionSource
from app.models.base import Base, IdMixin, TimestampMixin, pg_enum


class Client(IdMixin, TimestampMixin, Base):
    __tablename__ = "clients"
    __table_args__ = (
        Index(
            "uq_clients_single_unknown",
            "is_unknown",
            unique=True,
            postgresql_where=text("is_unknown"),
        ),
    )

    name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str | None] = mapped_column(String(254), unique=True)
    country: Mapped[str | None] = mapped_column(CHAR(2))
    currency: Mapped[str] = mapped_column(CHAR(3))
    is_unknown: Mapped[bool] = mapped_column(default=False)
    source: Mapped[TransactionSource] = mapped_column(
        pg_enum(TransactionSource, "transaction_source")
    )
