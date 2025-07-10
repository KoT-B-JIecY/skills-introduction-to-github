# UC Shop Telegram Bot (aiogram)
# Основной функционал: меню, покупка UC, FSM, мультиязычность, интеграция с PostgreSQL

import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.filters import CommandStart, Command
from aiogram.utils.i18n import I18n, gettext as _
import asyncpg
import os

# --- Конфиг ---
BOT_TOKEN = os.getenv("UC_BOT_TOKEN", "YOUR_UC_BOT_TOKEN")
POSTGRES_DSN = os.getenv("UC_POSTGRES_DSN", "postgresql://user:pass@localhost:5432/ucshop")

# --- Мультиязычность ---
i18n = I18n(path="locales", default_locale="ru", domain="messages")

# --- FSM ---
class BuyUC(StatesGroup):
    choosing_amount = State()
    confirming = State()

# --- Клавиатуры ---
def main_menu(lang="ru"):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(_("Купить UC", locale=lang)), KeyboardButton(_("Цены", locale=lang))],
            [KeyboardButton(_("Профиль", locale=lang)), KeyboardButton(_("Поддержка", locale=lang))],
            [KeyboardButton(_("Акции", locale=lang))],
        ],
        resize_keyboard=True
    )

def uc_amount_keyboard(lang="ru"):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="60 UC", callback_data="uc_60"), InlineKeyboardButton(text="300 UC", callback_data="uc_300")],
            [InlineKeyboardButton(text="600 UC", callback_data="uc_600"), InlineKeyboardButton(text="1800 UC", callback_data="uc_1800")],
            [InlineKeyboardButton(text=_("Назад", locale=lang), callback_data="back_menu")],
        ]
    )

# --- Бот и Диспетчер ---
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# --- DB ---
db_pool = None
async def get_db():
    global db_pool
    if db_pool is None:
        db_pool = await asyncpg.create_pool(dsn=POSTGRES_DSN)
    return db_pool

# --- Хендлеры ---
@dp.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    lang = message.from_user.language_code or "ru"
    await message.answer(_("Добро пожаловать в UC Shop!"), reply_markup=main_menu(lang))

@dp.message(lambda m: m.text in [_("Купить UC", locale="ru"), _( "Купить UC", locale="en"), _( "Купить UC", locale="ar")])
async def buy_uc(message: types.Message, state: FSMContext):
    lang = message.from_user.language_code or "ru"
    await message.answer(_("Выберите номинал UC:"), reply_markup=uc_amount_keyboard(lang))
    await state.set_state(BuyUC.choosing_amount)

@dp.callback_query(lambda c: c.data.startswith("uc_"))
async def uc_amount_chosen(callback: types.CallbackQuery, state: FSMContext):
    amount = int(callback.data.split("_")[1])
    await state.update_data(uc_amount=amount)
    await callback.message.answer(_(f"Вы выбрали {amount} UC. Для оформления заказа нажмите 'Оформить заказ'."))
    # Здесь можно добавить кнопку "Оформить заказ"
    await state.set_state(BuyUC.confirming)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "back_menu")
async def back_to_menu(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.from_user.language_code or "ru"
    await callback.message.answer(_("Главное меню"), reply_markup=main_menu(lang))
    await state.clear()
    await callback.answer()

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())