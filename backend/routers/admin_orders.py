"""Admin order management endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.db import get_db
from backend import models
from backend.schemas import OrderRead, OrderUpdate
from backend.dependencies import verify_admin_api_key

router = APIRouter(prefix="/admin/orders", tags=["admin-orders"], dependencies=[Depends(verify_admin_api_key)])


@router.get("/", response_model=List[OrderRead])
def admin_list_orders(db: Session = Depends(get_db)):
    return db.query(models.Order).order_by(models.Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderRead)
def admin_get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}", response_model=OrderRead)
def admin_update_order(order_id: int, order_in: OrderUpdate, db: Session = Depends(get_db)):
    order = db.query(models.Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    update_data = order_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(order, field, value)

    db.add(order)
    db.commit()
    db.refresh(order)
    return order