"""Crypto payment endpoints."""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from backend import crud, models
from backend.db import get_db
from backend.payments.crypto import crypto_provider
from backend.schemas import OrderRead

router = APIRouter(prefix="/crypto", tags=["crypto"])

SupportedCurrency = Literal["USDT", "BTC"]


@router.post("/invoice/{order_id}")
async def create_crypto_invoice(order_id: int, currency: SupportedCurrency, db: Session = Depends(get_db)):
    """Create crypto invoice for order."""
    order = db.query(models.Order).get(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != models.OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order already processed")

    # Use provider to generate payment address
    invoice = await crypto_provider.create_invoice(amount=float(order.amount), currency=currency, order_id=order.id)

    # Store payment in DB
    payment = crud.create_payment(
        db,
        order=order,
        provider=crypto_provider.name,
        amount=float(order.amount),
        currency=currency,
        meta={"invoice": invoice},
    )

    return {
        "order_id": order.id,
        "payment_id": payment.id,
        "currency": currency,
        "amount": invoice["amount"],
        "address": invoice["address"],
    }


# --------------------------------------------------
# Webhook (stub)
# --------------------------------------------------


@router.post("/webhook")
async def crypto_webhook(request: Request, db: Session = Depends(get_db)):
    """Webhook endpoint called by crypto provider."""
    payload = await request.json()
    parsed = await crypto_provider.parse_webhook(payload)

    invoice_id = parsed.get("invoice_id")
    status_str = parsed.get("status")
    tx_hash = parsed.get("tx_hash")

    if not invoice_id:
        raise HTTPException(status_code=400, detail="Invalid payload")

    # Find payment by invoice id in meta_json
    payment = (
        db.query(models.Payment)
        .filter(models.Payment.meta_json["invoice"]["invoice_id"].as_string() == invoice_id)
        .first()
    )

    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    # Map provider status to PaymentStatus
    if status_str in ("confirmed", "finished", "paid"):
        new_status = models.PaymentStatus.CONFIRMED
    elif status_str == "failed":
        new_status = models.PaymentStatus.FAILED
    else:
        new_status = models.PaymentStatus.PENDING

    crud.set_payment_status(db, payment, new_status, tx_hash=tx_hash)

    return {"ok": True}