"""Admin product management endpoints."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db import get_db
from backend import models
from backend.schemas import ProductRead, ProductCreate, ProductUpdate
from backend.dependencies import verify_admin_api_key

router = APIRouter(prefix="/admin/products", tags=["admin-products"], dependencies=[Depends(verify_admin_api_key)])


@router.get("/", response_model=List[ProductRead])
def admin_list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).order_by(models.Product.uc_amount).all()


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def admin_create_product(product_in: ProductCreate, db: Session = Depends(get_db)):
    product = models.Product(**product_in.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductRead)
def admin_update_product(product_id: int, product_in: ProductUpdate, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return None