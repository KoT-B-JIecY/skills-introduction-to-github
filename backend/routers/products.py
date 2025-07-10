"""Products API router."""

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.schemas import ProductRead
from backend import crud
from backend.db import get_db

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/", response_model=List[ProductRead])
def list_products(db: Session = Depends(get_db)):
    """Return list of active products."""
    products = crud.get_products(db)
    return products