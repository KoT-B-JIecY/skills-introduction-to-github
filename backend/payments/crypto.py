"""Stub crypto payment provider (NOWPayments-like) for USDT/BTC."""

import os
from typing import Any, Dict

import httpx

from backend.payments.base import PaymentProvider, PaymentProviderError


class CryptoStubProvider(PaymentProvider):
    """Simple stub provider that simulates crypto invoices."""

    name = "crypto_stub"

    def __init__(self) -> None:
        self.api_key = os.getenv("CRYPTO_API_KEY", "stub")
        self.base_url = os.getenv("CRYPTO_API_URL", "https://api.mockcrypto.local")
        # If we use real API, we set above accordingly.

    async def create_invoice(self, amount: float, currency: str, order_id: int) -> Dict[str, Any]:
        # For stub, return fake address and amount
        # In production, call external API here.
        address = f"mock_{currency.lower()}_address_{order_id}"
        invoice_id = f"invoice_{order_id}"
        return {
            "invoice_id": invoice_id,
            "address": address,
            "amount": amount,
            "currency": currency,
        }

    async def parse_webhook(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # For stub we expect data = {"invoice_id":..., "status": "confirmed", "tx_hash": "..."}
        return {
            "invoice_id": data.get("invoice_id"),
            "status": data.get("status"),
            "tx_hash": data.get("tx_hash"),
        }


# Singleton provider instance
crypto_provider = CryptoStubProvider()