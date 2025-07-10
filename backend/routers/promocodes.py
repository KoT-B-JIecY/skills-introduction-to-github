"""Promocode API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import crud, models
from backend.db import get_db
from backend.schemas import PromocodeCreate, PromocodeRead, PromocodeRedeem
from backend.dependencies import verify_admin_api_key

router = APIRouter(prefix="/promo", tags=["promo"])


@router.post("/create", response_model=PromocodeRead, dependencies=[Depends(verify_admin_api_key)])
def admin_create_promo(promo_in: PromocodeCreate, db: Session = Depends(get_db)):
    promo = crud.create_promocode(
        db,
        code=promo_in.code,
        discount_pct=promo_in.discount_pct,
        max_uses=promo_in.max_uses,
        expires_at=promo_in.expires_at,
    )
    db.commit()
    db.refresh(promo)
    return promo


@router.post("/redeem")
def redeem_promo(body: PromocodeRedeem, db: Session = Depends(get_db)):
    user = crud.get_user_by_tg(db, body.tg_id)
    if not user:
        user = crud.create_user(db, body.tg_id)

    try:
        promo = crud.redeem_promocode(db, user, body.code)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.commit()
    return {"ok": True, "discount_pct": promo.discount_pct, "balance": float(user.balance)}