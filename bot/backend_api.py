"""Async helper functions to communicate with FastAPI backend."""

import os
from typing import List, Dict, Any, Optional

import httpx

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

_CLIENT: Optional[httpx.AsyncClient] = None


async def get_client() -> httpx.AsyncClient:
    global _CLIENT
    if _CLIENT is None or _CLIENT.is_closed:
        _CLIENT = httpx.AsyncClient(base_url=BACKEND_URL, timeout=10.0)
    return _CLIENT


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

async def fetch_products() -> List[Dict[str, Any]]:
    client = await get_client()
    resp = await client.get("/products/")
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

async def create_order(tg_id: int, product_id: int, qty: int = 1) -> Dict[str, Any]:
    client = await get_client()
    resp = await client.post(
        "/orders/", json={"tg_id": tg_id, "product_id": product_id, "qty": qty}
    )
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Crypto payments
# ---------------------------------------------------------------------------


async def create_crypto_invoice(order_id: int, currency: str = "USDT") -> Dict[str, Any]:
    client = await get_client()
    resp = await client.post(f"/crypto/invoice/{order_id}?currency={currency}")
    resp.raise_for_status()
    return resp.json()

# ---------------------------------------------------------------------------
# Promo & Referral
# ---------------------------------------------------------------------------


async def redeem_promo(tg_id: int, code: str):
    client = await get_client()
    resp = await client.post("/promo/redeem", json={"tg_id": tg_id, "code": code})
    resp.raise_for_status()
    return resp.json()


async def link_referral(inviter_code: str, tg_id: int):
    client = await get_client()
    resp = await client.post(f"/referrals/link/{inviter_code}/{tg_id}")
    resp.raise_for_status()
    return resp.json()