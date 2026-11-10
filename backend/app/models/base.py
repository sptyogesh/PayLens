"""Declarative base and shared column helpers."""

import uuid
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any, ClassVar

from sqlalchemy import DateTime, Enum, Numeric, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

MONEY = Numeric(14, 2)
RATE = Numeric(14, 6)


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict[Any, Any]] = {
        Decimal: MONEY,
        datetime: DateTime(timezone=True),
    }


class IdMixin:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())


def pg_enum(enum_cls: type[StrEnum], name: str) -> Enum:
    """A PostgreSQL enum that stores the enum *values* (e.g. "paypal_sandbox")."""
    return Enum(enum_cls, name=name, values_callable=lambda members: [m.value for m in members])
