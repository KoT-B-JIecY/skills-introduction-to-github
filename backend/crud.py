"""CRUD helper functions for DB operations."""

from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

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

# ---------------------------------------------------------------------------
# Promocodes
# ---------------------------------------------------------------------------


def create_promocode(db: Session, code: str, discount_pct: int, max_uses: int = 0, expires_at=None) -> models.Promocode:
    promo = models.Promocode(
        code=code.upper(),
        discount_pct=discount_pct,
        max_uses=max_uses,
        expires_at=expires_at,
    )
    db.add(promo)
    db.flush()
    return promo


def redeem_promocode(db: Session, user: models.User, code: str) -> models.Promocode:
    promo = (
        db.query(models.Promocode)
        .filter(models.Promocode.code == code.upper())
        .first()
    )
    if not promo:
        raise ValueError("Promo not found")
    if promo.expires_at and promo.expires_at < func.now():
        raise ValueError("Promo expired")
    if promo.max_uses > 0 and promo.used_times >= promo.max_uses:
        raise ValueError("Promo fully used")

    promo.used_times += 1
    user.balance += promo.discount_pct  # simplistic: just store as balance credit

    db.add_all([promo, user])
    return promo


# ---------------------------------------------------------------------------
# Referrals
# ---------------------------------------------------------------------------


def add_referral(db: Session, inviter_code: str, invited_tg_id: int) -> models.Referral:
    inviter = db.query(models.User).filter(models.User.referral_code == inviter_code).first()
    if not inviter:
        raise ValueError("Inviter not found")

    invited = get_user_by_tg(db, invited_tg_id)
    if not invited:
        invited = create_user(db, invited_tg_id)

    # prevent self referral or duplicates
    if invited.id == inviter.id:
        raise ValueError("Cannot refer yourself")
    existing = (
        db.query(models.Referral)
        .filter(models.Referral.inviter_id == inviter.id, models.Referral.invited_id == invited.id)
        .first()
    )
    if existing:
        return existing

    ref = models.Referral(inviter_id=inviter.id, invited_id=invited.id, bonus=0)
    db.add(ref)
    inviter.balance += 1  # bonus point for inviter
    db.add(inviter)
    return ref

# ---------------------------------------------------------------------------
# Tournaments
# ---------------------------------------------------------------------------


def create_tournament(db: Session, name: str, prize_pool: float) -> models.Tournament:
    t = models.Tournament(name=name, prize_pool=prize_pool)
    db.add(t)
    db.flush()
    return t


def join_tournament(db: Session, tournament: models.Tournament, user: models.User):
    existing = (
        db.query(models.TournamentParticipant)
        .filter(
            models.TournamentParticipant.tournament_id == tournament.id,
            models.TournamentParticipant.user_id == user.id,
        )
        .first()
    )
    if existing:
        return existing

    p = models.TournamentParticipant(tournament_id=tournament.id, user_id=user.id)
    db.add(p)
    return p


def draw_tournament_winners(db: Session, tournament: models.Tournament, winners_count: int = 3):
    participants = [p.user_id for p in tournament.participants]
    if not participants:
        raise ValueError("No participants")

    import random

    winners_ids = random.sample(participants, min(len(participants), winners_count))
    tournament.winners_json = {"winners": winners_ids}
    db.add(tournament)
    return winners_ids