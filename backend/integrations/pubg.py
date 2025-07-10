"""Integration with PUBG UC delivery (stub)."""

import os
import httpx

PUBG_API_KEY = os.getenv("PUBG_API_KEY", "stub")
PUBG_API_URL = os.getenv("PUBG_API_URL", "https://api.mockpubg.local")


async def deliver_uc(tg_id: int, uc_amount: int) -> str:
    """Send UC to user. Returns delivery code or transaction id."""
    # For mock, just return fake code.
    # Real implementation would POST to provider.
    return f"DELIVERY_{tg_id}_{uc_amount}"