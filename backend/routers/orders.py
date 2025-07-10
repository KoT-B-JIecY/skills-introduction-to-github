"""Orders API router."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.schemas import OrderCreate, OrderRead
from backend import crud, models
from backend.db import get_db
from backend.utils.notifications import notify_admin

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(order_in: OrderCreate, db: Session = Depends(get_db)):
    """Create order for user."""
    # Get product
    product = db.query(models.Product).get(order_in.product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        order = crud.create_order(db, tg_id=order_in.tg_id, product=product, qty=order_in.qty)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.commit()
    db.refresh(order)

    import asyncio

    asyncio.create_task(
        notify_admin(
            f"🆕 New Order #{order.id}\nUser: {order.user_id}\nProduct: {product.title} x{order.qty}\nAmount: ${order.amount}"
        )
    )

    return order