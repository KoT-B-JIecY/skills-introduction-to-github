"""Tournament API."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend import crud, models
from backend.db import get_db
from backend.dependencies import verify_admin_api_key

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.post("/", dependencies=[Depends(verify_admin_api_key)])
def admin_create_tournament(name: str, prize_pool: float, db: Session = Depends(get_db)):
    t = crud.create_tournament(db, name, prize_pool)
    db.commit()
    db.refresh(t)
    return {"id": t.id}


@router.get("/", response_model=List[dict])
def list_tournaments(db: Session = Depends(get_db)):
    items = db.query(models.Tournament).all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "prize_pool": float(t.prize_pool),
            "participants": len(t.participants),
            "winners": t.winners_json,
        }
        for t in items
    ]


@router.post("/{tournament_id}/join")
def join_tournament(tournament_id: int, tg_id: int, db: Session = Depends(get_db)):
    t = db.query(models.Tournament).get(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    user = crud.get_user_by_tg(db, tg_id)
    if not user:
        user = crud.create_user(db, tg_id)
    crud.join_tournament(db, t, user)
    db.commit()
    return {"ok": True}


@router.post("/{tournament_id}/draw", dependencies=[Depends(verify_admin_api_key)])
def draw_winners(tournament_id: int, winners: int = 3, db: Session = Depends(get_db)):
    t = db.query(models.Tournament).get(tournament_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tournament not found")
    winner_ids = crud.draw_tournament_winners(db, t, winners)
    db.commit()
    return {"winners": winner_ids}