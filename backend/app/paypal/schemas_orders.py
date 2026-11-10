"""Pydantic models for Orders v2 create/capture responses (research R1, R3, R6, R7)."""

from datetime import datetime

from pydantic import Field

from app.paypal.schemas import AmountWithCurrency, PayPalModel


class CreateOrderResponse(PayPalModel):
    id: str
    status: str


class SellerReceivableBreakdown(PayPalModel):
    gross_amount: AmountWithCurrency
    paypal_fee: AmountWithCurrency | None = None
    net_amount: AmountWithCurrency | None = None


class Capture(PayPalModel):
    id: str
    status: str
    amount: AmountWithCurrency
    seller_receivable_breakdown: SellerReceivableBreakdown | None = None
    create_time: datetime | None = None


class Payments(PayPalModel):
    captures: list[Capture] = Field(default_factory=list)


class PurchaseUnit(PayPalModel):
    payments: Payments | None = None


class OrderPayerName(PayPalModel):
    given_name: str | None = None
    surname: str | None = None


class OrderPayerAddress(PayPalModel):
    country_code: str | None = None


class OrderPayer(PayPalModel):
    email_address: str | None = None
    name: OrderPayerName | None = None
    address: OrderPayerAddress | None = None


class CaptureResponse(PayPalModel):
    id: str
    status: str
    purchase_units: list[PurchaseUnit] = Field(default_factory=list)
    payer: OrderPayer | None = None

    def first_capture(self) -> Capture | None:
        for unit in self.purchase_units:
            if unit.payments and unit.payments.captures:
                return unit.payments.captures[0]
        return None
