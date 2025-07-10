"""Common FastAPI dependencies."""

import os

from fastapi import Header, HTTPException, status

ADMIN_API_KEY = os.getenv("ADMIN_API_KEY", "changeme")


def verify_admin_api_key(x_api_key: str = Header(..., alias="X-API-KEY")) -> None:
    """Simple API key header authentication for admin routes."""
    if x_api_key != ADMIN_API_KEY:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")