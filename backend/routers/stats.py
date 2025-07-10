"""Stats API for admin graphs."""

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.db import get_db
from backend.dependencies import verify_admin_api_key
from backend import models

router = APIRouter(prefix="/stats", tags=["stats"], dependencies=[Depends(verify_admin_api_key)])


@router.get("/sales/day")
def sales_per_day(days: int = 7, db: Session = Depends(get_db)):
    since = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(func.date_trunc("day", models.Order.created_at).label("day"), func.sum(models.Order.amount))
        .filter(models.Order.status == models.OrderStatus.PAID, models.Order.created_at >= since)
        .group_by("day")
        .order_by("day")
        .all()
    )
    return [{"day": row[0].date().isoformat(), "amount": float(row[1])} for row in rows]


@router.get("/popular-products")
def popular_products(limit: int = 5, db: Session = Depends(get_db)):
    rows = (
        db.query(models.Product.title, func.count(models.Order.id))
        .join(models.Order, models.Order.product_id == models.Product.id)
        .filter(models.Order.status == models.OrderStatus.PAID)
        .group_by(models.Product.title)
        .order_by(func.count(models.Order.id).desc())
        .limit(limit)
        .all()
    )
    return [{"title": r[0], "count": r[1]} for r in rows]