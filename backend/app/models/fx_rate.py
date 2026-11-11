"""fx_rates table: cached mid-market rates to INR, one per (currency, IST date) (002 R2)."""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CHAR, CheckConstraint, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import RATE, Base, IdMixin, TimestampMixin


class FxRate(IdMixin, TimestampMixin, Base):
    __tablename__ = "fx_rates"
    __table_args__ = (
        UniqueConstraint("currency", "rate_date", name="uq_fx_rates_currency_date"),
        CheckConstraint("rate > 0", name="ck_fx_rates_rate_positive"),
        CheckConstraint("published_date <= rate_date", name="ck_fx_rates_published_not_after"),
    )

    currency: Mapped[str] = mapped_column(CHAR(3))
    rate_date: Mapped[date]
    published_date: Mapped[date]
    rate: Mapped[Decimal] = mapped_column(RATE)
    source: Mapped[str] = mapped_column(String(32))
    fetched_at: Mapped[datetime]
