"""Pydantic models for PayPal responses (Principle IV). Only the fields we use."""

from pydantic import BaseModel, ConfigDict


class PayPalModel(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class TokenResponse(PayPalModel):
    access_token: str
    expires_in: int
