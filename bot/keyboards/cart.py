from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def cart_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text="✅ Checkout", callback_data="cart:checkout")],
        [InlineKeyboardButton(text="❌ Cancel", callback_data="cart:cancel")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)