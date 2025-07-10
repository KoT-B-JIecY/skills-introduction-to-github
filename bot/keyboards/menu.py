from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu() -> InlineKeyboardMarkup:
    """Return the main menu inline keyboard."""
    buttons = [
        [InlineKeyboardButton(text="🛒 Buy UC", callback_data="menu:buy_uc")],
        [InlineKeyboardButton(text="💲 Prices", callback_data="menu:prices")],
        [InlineKeyboardButton(text="📞 Support", callback_data="menu:support")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="menu:profile")],
        [InlineKeyboardButton(text="🎁 Promotions", callback_data="menu:promotions")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)