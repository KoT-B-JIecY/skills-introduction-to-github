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


class ProductCreate(ProductBase):
    is_active: bool = True


class ProductUpdate(BaseModel):
    title: str | None = None
    uc_amount: int | None = None
    price_usd: float | None = None
    is_active: bool | None = None


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


# ---------------------------------------------------------------------------
# Order update (admin)
# ---------------------------------------------------------------------------


class OrderUpdate(BaseModel):
    status: str | None = None


# ---------------------------------------------------------------------------
# Promocode schemas
# ---------------------------------------------------------------------------


class PromocodeCreate(BaseModel):
    code: str
    discount_pct: int = Field(..., ge=1, le=100)
    max_uses: int = 0
    expires_at: datetime | None = None


class PromocodeRead(BaseModel):
    id: int
    code: str
    discount_pct: int
    max_uses: int
    used_times: int
    expires_at: datetime | None

    class Config:
        orm_mode = True


class PromocodeRedeem(BaseModel):
    tg_id: int
    code: str