from fastapi import FastAPI, Depends

from backend.db import engine, get_db
from backend import models  # noqa: F401  # ensure models are imported and metadata is ready
from sqlalchemy.orm import Session

# Create DB tables at startup (dev only; use Alembic migrations in production)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="UC Bot Backend API")


# ---------------------------------------------------------------------------
# Startup tasks
# ---------------------------------------------------------------------------


@app.on_event("startup")
def _ensure_default_products() -> None:
    """Populate DB with default UC products if empty (dev/demo)."""
    from backend.db import SessionLocal

    with SessionLocal() as db:
        if db.query(models.Product).count() == 0:
            default_products = [
                {"title": "60 UC", "uc_amount": 60, "price_usd": 1.0},
                {"title": "300 UC", "uc_amount": 300, "price_usd": 5.0},
                {"title": "600 UC", "uc_amount": 600, "price_usd": 9.0},
                {"title": "1800 UC", "uc_amount": 1800, "price_usd": 24.0},
            ]
            for p in default_products:
                product = models.Product(**p)
                db.add(product)
            db.commit()


# Routers
from backend.routers.products import router as products_router
from backend.routers.orders import router as orders_router
from backend.routers.crypto_payments import router as crypto_router
from backend.routers.admin_products import router as admin_products_router
from backend.routers.admin_orders import router as admin_orders_router
from backend.routers.promocodes import router as promo_router
from backend.routers.referrals import router as referral_router
from backend.routers.tournaments import router as tournament_router
from backend.routers.stats import router as stats_router

app.include_router(products_router)
app.include_router(orders_router)
app.include_router(crypto_router)
app.include_router(admin_products_router)
app.include_router(admin_orders_router)
app.include_router(promo_router)
app.include_router(referral_router)
app.include_router(tournament_router)
app.include_router(stats_router)


@app.get("/ping")
async def ping():
    return {"status": "ok"}


@app.get("/health")
async def health(db: Session = Depends(get_db)):
    """Simple DB connectivity healthcheck."""
    db.execute("SELECT 1")
    return {"db": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)