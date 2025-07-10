import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from dotenv import load_dotenv

# Routers
from bot.handlers.menu import router as menu_router

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "SET_YOUR_TOKEN")


async def main() -> None:
    """Entry point for the Telegram bot."""
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Include routers
    dp.include_router(menu_router)

    print("Bot polling started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped!")