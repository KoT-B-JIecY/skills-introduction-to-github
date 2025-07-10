"""Referral API."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import crud, models
from backend.db import get_db

router = APIRouter(prefix="/referrals", tags=["referrals"])


@router.post("/link/{inviter_code}/{tg_id}")
def link_referral(inviter_code: str, tg_id: int, db: Session = Depends(get_db)):
    try:
        ref = crud.add_referral(db, inviter_code, tg_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    db.commit()
    return {"ok": True}