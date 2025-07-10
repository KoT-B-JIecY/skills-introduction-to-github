"""Orders API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.schemas import OrderCreate, OrderRead
from backend import crud, models
from backend.db import get_db

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)):
    """Create order for user."""
    # Get product
    product = db.query(models.Product).get(order_in.product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")

    order = crud.create_order(db, tg_id=order_in.tg_id, product=product, qty=order_in.qty)
    return order