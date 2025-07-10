from aiogram import Router, F, types
from aiogram.filters import CommandStart
from bot.keyboards.menu import main_menu
from bot.keyboards.buy_uc import buy_uc_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message):
    """Send main menu on /start."""
    await message.answer("Welcome! Choose an option:", reply_markup=main_menu())


@router.callback_query(F.data.startswith("menu:"))
async def process_menu(callback: types.CallbackQuery):
    """Handle main menu selections."""
    action = callback.data.split(":", 1)[1]

    if action == "buy_uc":
        await callback.message.edit_text(
            "Select UC amount:", reply_markup=buy_uc_keyboard()
        )
    elif action == "prices":
        await callback.message.edit_text(
            "Current prices:\n60 UC — $1\n300 UC — $5\n600 UC — $9\n1800 UC — $24",
            reply_markup=main_menu(),
        )
    elif action == "support":
        await callback.message.edit_text(
            "Support: @YourSupportUsername", reply_markup=main_menu()
        )
    elif action == "profile":
        await callback.message.edit_text(
            f"Profile:\nID: {callback.from_user.id}", reply_markup=main_menu()
        )
    elif action == "promotions":
        await callback.message.edit_text(
            "No promotions yet!", reply_markup=main_menu()
        )
    elif action == "main":
        await callback.message.edit_text("Main menu:", reply_markup=main_menu())

    await callback.answer()


@router.callback_query(F.data.startswith("buy_uc:"))
async def process_buy_uc(callback: types.CallbackQuery):
    """Handle UC amount selection."""
    amount_str = callback.data.split(":", 1)[1]
    try:
        amount = int(amount_str)
    except ValueError:
        await callback.answer("Invalid amount", show_alert=True)
        return

    await callback.answer(f"You selected {amount} UC", show_alert=True)

    # TODO: Add to cart or proceed to checkout in future steps