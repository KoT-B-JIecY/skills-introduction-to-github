from fastapi import FastAPI, Depends

from backend.db import engine, get_db
from backend import models  # noqa: F401  # ensure models are imported and metadata is ready
from sqlalchemy.orm import Session

# Create DB tables at startup (dev only; use Alembic migrations in production)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="UC Bot Backend API")


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