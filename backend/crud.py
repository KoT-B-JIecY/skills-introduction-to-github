"""CRUD helper functions for DB operations."""

from typing import List, Optional

from sqlalchemy.orm import Session

from backend import models


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

def get_products(db: Session, active_only: bool = True) -> List[models.Product]:
    query = db.query(models.Product)
    if active_only:
        query = query.filter(models.Product.is_active.is_(True))
    return query.order_by(models.Product.uc_amount).all()


def get_product_by_uc(db: Session, uc_amount: int) -> Optional[models.Product]:
    return (
        db.query(models.Product)
        .filter(models.Product.uc_amount == uc_amount, models.Product.is_active.is_(True))
        .first()
    )

# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------

def get_user_by_tg(db: Session, tg_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.tg_id == tg_id).first()


def create_user(db: Session, tg_id: int) -> models.User:
    user = models.User(tg_id=tg_id)
    db.add(user)
    db.flush()  # get id
    return user

# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

def create_order(db: Session, tg_id: int, product: models.Product, qty: int = 1) -> models.Order:
    user = get_user_by_tg(db, tg_id)
    if not user:
        user = create_user(db, tg_id)

    amount = float(product.price_usd) * qty

    order = models.Order(
        user_id=user.id,
        product_id=product.id,
        qty=qty,
        amount=amount,
    )
    db.add(order)
    db.flush()
    return order

# ---------------------------------------------------------------------------
# Payments
# ---------------------------------------------------------------------------


def create_payment(
    db: Session,
    order: models.Order,
    provider: str,
    amount: float,
    currency: str,
    meta: dict,
) -> models.Payment:
    payment = models.Payment(
        order_id=order.id,
        user_id=order.user_id,
        provider=provider,
        amount=amount,
        currency=currency,
        meta_json=meta,
    )
    db.add(payment)
    db.flush()
    return payment


def set_payment_status(db: Session, payment: models.Payment, status: models.PaymentStatus, tx_hash: str | None = None):
    payment.status = status
    payment.meta_json = {**(payment.meta_json or {}), "tx_hash": tx_hash}
    db.add(payment)

    if status == models.PaymentStatus.CONFIRMED:
        # update order status if all payments confirmed
        order = payment.order
        order.status = models.OrderStatus.PAID
        db.add(order)