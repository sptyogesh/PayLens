"""POST /pay/orders and POST /pay/orders/{order_id}/capture, both rate limited (research R8)."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_fx_gateway, get_gateway, rate_limit
from app.common.constants import RATE_LIMIT_PAY
from app.db import get_session_factory
from app.fx import FxGateway
from app.paypal import PayPalGateway
from app.schemas.pay import CaptureOut, OrderId, PayOrderIn, PayOrderOut
from app.services.checkout_service import capture_and_record, create_order

router = APIRouter(
    prefix="/pay", tags=["pay"], dependencies=[Depends(rate_limit("pay", RATE_LIMIT_PAY))]
)


@router.post("/orders", status_code=201)
def post_order(
    body: PayOrderIn, gateway: Annotated[PayPalGateway, Depends(get_gateway)]
) -> PayOrderOut:
    return PayOrderOut(order_id=create_order(gateway, body))


@router.post("/orders/{order_id}/capture")
def post_capture(
    order_id: Annotated[OrderId, Path()],
    gateway: Annotated[PayPalGateway, Depends(get_gateway)],
    factory: Annotated[sessionmaker[Session], Depends(get_session_factory)],
    fx: Annotated[FxGateway, Depends(get_fx_gateway)],
) -> CaptureOut:
    return capture_and_record(gateway, factory, order_id, fx)
