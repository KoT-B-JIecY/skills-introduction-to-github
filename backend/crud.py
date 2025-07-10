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