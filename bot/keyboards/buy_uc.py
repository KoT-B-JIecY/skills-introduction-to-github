from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

UC_AMOUNTS: list[int] = [60, 300, 600, 1800]


def buy_uc_keyboard() -> InlineKeyboardMarkup:
    """Return an inline keyboard to choose an UC amount."""
    buttons = [
        [InlineKeyboardButton(text=f"{amount} UC", callback_data=f"buy_uc:{amount}")]
        for amount in UC_AMOUNTS
    ]
    # Back button to main menu
    buttons.append([InlineKeyboardButton(text="⬅️ Back", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)