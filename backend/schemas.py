"""Pydantic models (schemas) for request / response bodies."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Product schemas
# ---------------------------------------------------------------------------


class ProductBase(BaseModel):
    title: str
    uc_amount: int
    price_usd: float


class ProductRead(ProductBase):
    id: int
    is_active: bool

    class Config:
        orm_mode = True


# ---------------------------------------------------------------------------
# Order schemas
# ---------------------------------------------------------------------------


class OrderCreate(BaseModel):
    tg_id: int = Field(..., description="Telegram user id")
    product_id: int = Field(..., description="Product id")
    qty: int = Field(1, ge=1)


class OrderRead(BaseModel):
    id: int
    user_id: int
    product_id: int
    qty: int
    status: str
    amount: float
    created_at: datetime

    class Config:
        orm_mode = True