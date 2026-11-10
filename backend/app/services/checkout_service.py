"""Create and capture /pay orders, and record the payment at once (FR-032, FR-033)."""

import logging

from sqlalchemy.exc import SQLAlchemyError

from app.common.dates import utc_now
from app.common.types import TransactionStatus
from app.fx import FxGateway
from app.paypal.gateway import PayPalGateway
from app.paypal.mapper import from_capture
from app.paypal.sync import SessionFactory
from app.paypal.upsert import upsert_transaction
from app.schemas.common import MoneyOut
from app.schemas.pay import CaptureOut, PayOrderIn
from app.services.leakage_service import safe_recalculate

logger = logging.getLogger(__name__)


def create_order(gateway: PayPalGateway, order: PayOrderIn) -> str:
    return gateway.create_order(order.amount, order.currency, order.description)


def capture_and_record(
    gateway: PayPalGateway, factory: SessionFactory, order_id: str, fx: FxGateway
) -> CaptureOut:
    """Capture at PayPal, then store. If storing fails the payment still happened: the next
    sync records it, so the client sees the confirmation with recorded=false."""
    dto = from_capture(gateway.capture_order(order_id), utc_now())
    recorded = True
    try:
        with factory() as session:
            upsert_transaction(session, dto)
            session.commit()
    except SQLAlchemyError as error:
        recorded = False
        logger.error("Captured payment could not be recorded: %s", type(error).__name__)
    if recorded:
        safe_recalculate(factory, fx)  # FR-020
    return CaptureOut(
        transaction_id=dto.paypal_transaction_id,
        order_id=order_id,
        status="pending" if dto.status is TransactionStatus.PENDING else "completed",
        gross=MoneyOut.of(dto.gross, dto.currency),
        recorded=recorded,
    )
