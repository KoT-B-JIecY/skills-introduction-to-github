"""SQLAlchemy ORM models for the UC Bot backend."""

from enum import Enum
from typing import List

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum as PgEnum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all models."""

    repr_cols_num = 3  # number of columns to show in __repr__

    def __repr__(self) -> str:  # pragma: no cover
        column_values = (
            f"{c.key}={getattr(self, c.key)!r}" for c in self.__table__.columns[: self.repr_cols_num]
        )
        return f"<{self.__class__.__name__}({' ,'.join(column_values)})>"


# ---------------------------------------------------------------------------
# Enum definitions
# ---------------------------------------------------------------------------


class OrderStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    lang: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    referral_code: Mapped[str | None] = mapped_column(String(32), unique=True)
    balance: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    orders: Mapped[List["Order"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    payments: Mapped[List["Payment"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    invited_referrals: Mapped[List["Referral"]] = relationship(
        back_populates="inviter", foreign_keys="Referral.inviter_id", cascade="all, delete-orphan"
    )
    invited_by: Mapped[List["Referral"]] = relationship(
        back_populates="invited", foreign_keys="Referral.invited_id", cascade="all, delete-orphan"
    )


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    uc_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    price_usd: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    orders: Mapped[List["Order"]] = relationship(back_populates="product", cascade="all, delete-orphan")


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[OrderStatus] = mapped_column(PgEnum(OrderStatus), default=OrderStatus.PENDING)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    pay_provider: Mapped[str | None] = mapped_column(String(50))
    tx_hash: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="orders")
    product: Mapped["Product"] = relationship(back_populates="orders")
    payments: Mapped[List["Payment"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(10), nullable=False)
    status: Mapped[PaymentStatus] = mapped_column(PgEnum(PaymentStatus), default=PaymentStatus.PENDING)
    meta_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    order: Mapped["Order"] = relationship(back_populates="payments")
    user: Mapped["User"] = relationship(back_populates="payments")


class Promocode(Base):
    __tablename__ = "promocodes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    discount_pct: Mapped[int] = mapped_column(Integer, nullable=False)
    max_uses: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    used_times: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expires_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    invited_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    bonus: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    inviter: Mapped["User"] = relationship("User", foreign_keys=[inviter_id], back_populates="invited_referrals")
    invited: Mapped["User"] = relationship("User", foreign_keys=[invited_id], back_populates="invited_by")


class Tournament(Base):
    __tablename__ = "tournaments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    prize_pool: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    winners_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())