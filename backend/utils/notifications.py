"""Send admin push notifications."""

import os
import httpx

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID")


async def notify_admin(message: str):
    if not BOT_TOKEN or not ADMIN_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": ADMIN_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=data, timeout=10)
        except Exception:
            pass