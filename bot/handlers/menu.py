from aiogram import Router, F, types
from aiogram.filters import CommandStart
from bot.keyboards.menu import main_menu
from bot.keyboards.buy_uc import buy_uc_keyboard
from bot.keyboards.cart import cart_keyboard

from bot import cart as cart_store
from bot import backend_api

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
    """Handle UC amount selection -> add to cart."""
    amount_str = callback.data.split(":", 1)[1]
    try:
        uc_amount = int(amount_str)
    except ValueError:
        await callback.answer("Invalid amount", show_alert=True)
        return

    # Fetch products from backend and find matching UC amount
    products = await backend_api.fetch_products()
    product = next((p for p in products if p["uc_amount"] == uc_amount), None)
    if not product:
        await callback.answer("Product not found", show_alert=True)
        return

    cart_store.set_cart(
        callback.from_user.id,
        cart_store.CartItem(
            product_id=product["id"],
            uc_amount=uc_amount,
            price_usd=float(product["price_usd"]),
        ),
    )

    text = (
        f"🛒 Cart:\n\n<code>{uc_amount} UC</code> — ${product['price_usd']}\n\n"
        "Press ✅ Checkout to place your order."
    )
    await callback.message.edit_text(text, reply_markup=cart_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("cart:"))
async def process_cart(callback: types.CallbackQuery):
    """Handle cart actions checkout/cancel."""
    action = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id
    cart_item = cart_store.get_cart(user_id)

    if not cart_item:
        await callback.answer("Cart is empty", show_alert=True)
        return

    if action == "cancel":
        cart_store.clear_cart(user_id)
        await callback.message.edit_text("Cart cleared.", reply_markup=buy_uc_keyboard())
        await callback.answer("Cancelled")
        return

    if action == "checkout":
        # Call backend to create order
        try:
            order = await backend_api.create_order(
                tg_id=user_id, product_id=cart_item.product_id, qty=cart_item.qty
            )
        except Exception as exc:
            await callback.answer(f"Error: {exc}", show_alert=True)
            return

        # Generate crypto invoice (USDT as default)
        try:
            invoice = await backend_api.create_crypto_invoice(order_id=order["id"], currency="USDT")
        except Exception as exc:
            await callback.answer(f"Order created but payment failed: {exc}", show_alert=True)
            return

        cart_store.clear_cart(user_id)

        payment_text = (
            f"✅ Order #{order['id']} created!\n\n"
            f"Send <b>{invoice['amount']} {invoice['currency']}</b> to the address below:\n"
            f"<code>{invoice['address']}</code>\n\n"
            "Once the transaction is confirmed, delivery will follow automatically."
        )

        await callback.message.edit_text(payment_text, reply_markup=main_menu())
        await callback.answer("Payment invoice generated")