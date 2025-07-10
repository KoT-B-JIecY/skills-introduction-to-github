"""
Main Telegram Bot Module for UC Bot
"""
import asyncio
import logging
from typing import Dict, Any

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command, StateFilter, Text
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from config.settings import settings, UC_PRODUCTS
from database.database import get_session
from database.models import User, Order, UCProduct, OrderStatus
from services.user_service import UserService
from services.order_service import OrderService
from services.payment_service import PaymentService
from utils.logger import logger
from utils.i18n import get_text, set_user_language


# Bot States
class OrderStates(StatesGroup):
    choosing_product = State()
    entering_pubg_id = State()
    entering_pubg_nickname = State()
    choosing_payment_method = State()
    confirming_order = State()


class ProfileStates(StatesGroup):
    editing_pubg_id = State()
    editing_nickname = State()


# Initialize bot
bot = Bot(
    token=settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

# Services
user_service = UserService()
order_service = OrderService()
payment_service = PaymentService()


def get_main_menu_keyboard(user_language: str = "ru") -> ReplyKeyboardMarkup:
    """Создать главное меню"""
    builder = ReplyKeyboardBuilder()
    
    # Main menu buttons
    builder.add(KeyboardButton(text=get_text("menu.buy_uc", user_language)))
    builder.add(KeyboardButton(text=get_text("menu.prices", user_language)))
    builder.add(KeyboardButton(text=get_text("menu.support", user_language)))
    builder.add(KeyboardButton(text=get_text("menu.profile", user_language)))
    builder.add(KeyboardButton(text=get_text("menu.promotions", user_language)))
    
    builder.adjust(2, 2, 1)
    
    return builder.as_markup(resize_keyboard=True)


def get_uc_products_keyboard(user_language: str = "ru") -> InlineKeyboardMarkup:
    """Создать клавиатуру с товарами UC"""
    builder = InlineKeyboardBuilder()
    
    for product in UC_PRODUCTS:
        # Format button text
        if product["bonus"] > 0:
            text = f"{product['amount']} UC + {product['bonus']} 🎁 - ${product['price']}"
        else:
            text = f"{product['amount']} UC - ${product['price']}"
        
        if product.get("popular"):
            text = f"🔥 {text}"
        
        builder.add(InlineKeyboardButton(
            text=text,
            callback_data=f"buy_uc:{product['amount']}:{product['price']}"
        ))
    
    builder.adjust(1)
    
    # Add back button
    builder.row(InlineKeyboardButton(
        text=get_text("button.back", user_language),
        callback_data="back_to_menu"
    ))
    
    return builder.as_markup()


def get_payment_methods_keyboard(order_id: int, user_language: str = "ru") -> InlineKeyboardMarkup:
    """Создать клавиатуру с методами оплаты"""
    builder = InlineKeyboardBuilder()
    
    # Available payment methods
    methods = [
        ("stripe", "💳", get_text("payment.card", user_language)),
        ("crypto", "₿", get_text("payment.crypto", user_language)),
        ("paypal", "💰", get_text("payment.paypal", user_language)),
        ("qiwi", "🥝", get_text("payment.qiwi", user_language)),
    ]
    
    for method_id, icon, name in methods:
        builder.add(InlineKeyboardButton(
            text=f"{icon} {name}",
            callback_data=f"pay:{method_id}:{order_id}"
        ))
    
    builder.adjust(2)
    
    # Add back button
    builder.row(InlineKeyboardButton(
        text=get_text("button.back", user_language),
        callback_data="back_to_products"
    ))
    
    return builder.as_markup()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    await state.clear()
    
    # Get or create user
    async with get_session() as session:
        user = await user_service.get_or_create_user(
            session=session,
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language_code=message.from_user.language_code
        )
        
        # Handle referral if present
        if message.text.startswith("/start ref_"):
            referral_code = message.text.split("_", 1)[1]
            await user_service.process_referral(session, user, referral_code)
    
    # Send welcome message
    welcome_text = get_text("welcome.message", user.language_code).format(
        name=message.from_user.first_name or "Друг"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(user.language_code)
    )


@router.message(Text(contains=["Купить UC", "Buy UC", "شراء UC"]))
async def show_uc_products(message: Message, state: FSMContext):
    """Show UC products"""
    await state.set_state(OrderStates.choosing_product)
    
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, message.from_user.id)
    
    text = get_text("products.choose", user.language_code)
    
    await message.answer(
        text,
        reply_markup=get_uc_products_keyboard(user.language_code)
    )


@router.callback_query(Text(startswith="buy_uc:"))
async def process_uc_selection(callback: CallbackQuery, state: FSMContext):
    """Process UC product selection"""
    # Parse callback data
    _, amount, price = callback.data.split(":")
    amount = int(amount)
    price = float(price)
    
    # Save selection to state
    await state.update_data(uc_amount=amount, uc_price=price)
    await state.set_state(OrderStates.entering_pubg_id)
    
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, callback.from_user.id)
    
    text = get_text("order.enter_pubg_id", user.language_code).format(
        amount=amount, price=price
    )
    
    # Pre-fill PUBG ID if user has it
    if user.pubg_id:
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text=get_text("button.use_saved_id", user.language_code),
            callback_data=f"use_saved_id:{user.pubg_id}"
        ))
        keyboard.row(InlineKeyboardButton(
            text=get_text("button.enter_new_id", user.language_code),
            callback_data="enter_new_id"
        ))
        reply_markup = keyboard.as_markup()
    else:
        reply_markup = None
    
    await callback.message.edit_text(text, reply_markup=reply_markup)


@router.callback_query(Text(startswith="use_saved_id:"))
async def use_saved_pubg_id(callback: CallbackQuery, state: FSMContext):
    """Use saved PUBG ID"""
    pubg_id = callback.data.split(":", 1)[1]
    await state.update_data(pubg_id=pubg_id)
    await state.set_state(OrderStates.entering_pubg_nickname)
    
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, callback.from_user.id)
    
    text = get_text("order.enter_pubg_nickname", user.language_code)
    
    # Pre-fill nickname if available
    if user.pubg_nickname:
        keyboard = InlineKeyboardBuilder()
        keyboard.add(InlineKeyboardButton(
            text=get_text("button.use_saved_nickname", user.language_code),
            callback_data=f"use_saved_nickname:{user.pubg_nickname}"
        ))
        keyboard.row(InlineKeyboardButton(
            text=get_text("button.enter_new_nickname", user.language_code),
            callback_data="enter_new_nickname"
        ))
        reply_markup = keyboard.as_markup()
    else:
        reply_markup = None
    
    await callback.message.edit_text(text, reply_markup=reply_markup)


@router.message(StateFilter(OrderStates.entering_pubg_id))
async def process_pubg_id(message: Message, state: FSMContext):
    """Process PUBG ID input"""
    pubg_id = message.text.strip()
    
    # Validate PUBG ID (basic validation)
    if len(pubg_id) < 9 or len(pubg_id) > 12 or not pubg_id.isdigit():
        async with get_session() as session:
            user = await user_service.get_user_by_telegram_id(session, message.from_user.id)
        
        await message.answer(get_text("error.invalid_pubg_id", user.language_code))
        return
    
    await state.update_data(pubg_id=pubg_id)
    await state.set_state(OrderStates.entering_pubg_nickname)
    
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, message.from_user.id)
    
    await message.answer(get_text("order.enter_pubg_nickname", user.language_code))


@router.message(StateFilter(OrderStates.entering_pubg_nickname))
async def process_pubg_nickname(message: Message, state: FSMContext):
    """Process PUBG nickname input"""
    nickname = message.text.strip()
    
    # Basic validation
    if len(nickname) < 3 or len(nickname) > 16:
        async with get_session() as session:
            user = await user_service.get_user_by_telegram_id(session, message.from_user.id)
        
        await message.answer(get_text("error.invalid_nickname", user.language_code))
        return
    
    await state.update_data(pubg_nickname=nickname)
    await state.set_state(OrderStates.choosing_payment_method)
    
    # Get order data
    data = await state.get_data()
    
    # Create order
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, message.from_user.id)
        
        order = await order_service.create_order(
            session=session,
            user_id=user.id,
            uc_amount=data["uc_amount"],
            price=data["uc_price"],
            pubg_id=data["pubg_id"],
            pubg_nickname=nickname
        )
        
        await state.update_data(order_id=order.id)
    
    # Show payment methods
    text = get_text("order.choose_payment", user.language_code).format(
        amount=data["uc_amount"],
        price=data["uc_price"],
        pubg_id=data["pubg_id"],
        nickname=nickname
    )
    
    await message.answer(
        text,
        reply_markup=get_payment_methods_keyboard(order.id, user.language_code)
    )


@router.callback_query(Text(startswith="pay:"))
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
    """Process payment method selection"""
    _, method, order_id = callback.data.split(":")
    order_id = int(order_id)
    
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, callback.from_user.id)
        order = await order_service.get_order_by_id(session, order_id)
        
        if not order or order.user_id != user.id:
            await callback.answer(get_text("error.order_not_found", user.language_code))
            return
        
        # Create payment
        payment_url = await payment_service.create_payment(
            session=session,
            order=order,
            method=method
        )
        
        if payment_url:
            # Send payment link
            keyboard = InlineKeyboardBuilder()
            keyboard.add(InlineKeyboardButton(
                text=get_text("button.pay_now", user.language_code),
                url=payment_url
            ))
            keyboard.row(InlineKeyboardButton(
                text=get_text("button.check_payment", user.language_code),
                callback_data=f"check_payment:{order.id}"
            ))
            
            text = get_text("payment.created", user.language_code).format(
                amount=order.total_uc,
                price=order.final_amount,
                method=method
            )
            
            await callback.message.edit_text(text, reply_markup=keyboard.as_markup())
        else:
            await callback.answer(get_text("error.payment_failed", user.language_code))


@router.callback_query(Text(startswith="check_payment:"))
async def check_payment_status(callback: CallbackQuery):
    """Check payment status"""
    order_id = int(callback.data.split(":")[1])
    
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, callback.from_user.id)
        order = await order_service.get_order_by_id(session, order_id)
        
        if not order or order.user_id != user.id:
            await callback.answer(get_text("error.order_not_found", user.language_code))
            return
        
        # Check payment status
        payment_status = await payment_service.check_payment_status(session, order)
        
        if payment_status == "completed":
            text = get_text("payment.success", user.language_code).format(
                amount=order.total_uc,
                pubg_id=order.pubg_id
            )
            
            if order.delivery_code:
                text += f"\n\n🎁 <b>Код UC:</b> <code>{order.delivery_code}</code>"
            
            await callback.message.edit_text(text)
        elif payment_status == "pending":
            await callback.answer(get_text("payment.still_pending", user.language_code))
        else:
            await callback.answer(get_text("payment.failed", user.language_code))


@router.message(Text(contains=["Цены", "Prices", "الأسعار"]))
async def show_prices(message: Message):
    """Show UC prices"""
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, message.from_user.id)
    
    text = get_text("prices.header", user.language_code) + "\n\n"
    
    for product in UC_PRODUCTS:
        if product["bonus"] > 0:
            text += f"💎 {product['amount']} UC + {product['bonus']} 🎁 - ${product['price']}\n"
        else:
            text += f"💎 {product['amount']} UC - ${product['price']}\n"
    
    text += f"\n{get_text('prices.footer', user.language_code)}"
    
    await message.answer(text)


@router.message(Text(contains=["Профиль", "Profile", "الملف الشخصي"]))
async def show_profile(message: Message):
    """Show user profile"""
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, message.from_user.id)
        stats = await user_service.get_user_stats(session, user.id)
    
    text = get_text("profile.info", user.language_code).format(
        username=user.username or "не указан",
        total_orders=stats["total_orders"],
        total_spent=stats["total_spent"],
        total_uc=stats["total_uc"],
        referral_code=user.referral_code or "не создан",
        referral_bonus=user.referral_bonus
    )
    
    # Profile management keyboard
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text=get_text("button.edit_pubg_data", user.language_code),
        callback_data="edit_pubg_data"
    ))
    keyboard.add(InlineKeyboardButton(
        text=get_text("button.order_history", user.language_code),
        callback_data="order_history"
    ))
    keyboard.add(InlineKeyboardButton(
        text=get_text("button.referral_info", user.language_code),
        callback_data="referral_info"
    ))
    keyboard.adjust(1)
    
    await message.answer(text, reply_markup=keyboard.as_markup())


@router.message(Text(contains=["Поддержка", "Support", "الدعم"]))
async def show_support(message: Message):
    """Show support information"""
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, message.from_user.id)
    
    text = get_text("support.info", user.language_code)
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text=get_text("button.contact_support", user.language_code),
        url="https://t.me/uc_support_bot"
    ))
    keyboard.add(InlineKeyboardButton(
        text=get_text("button.faq", user.language_code),
        callback_data="faq"
    ))
    keyboard.adjust(1)
    
    await message.answer(text, reply_markup=keyboard.as_markup())


@router.message(Text(contains=["Акции", "Promotions", "العروض"]))
async def show_promotions(message: Message):
    """Show current promotions"""
    async with get_session() as session:
        user = await user_service.get_user_by_telegram_id(session, message.from_user.id)
    
    text = get_text("promotions.current", user.language_code)
    
    # Add current promotions here
    text += "\n\n🔥 Скидка 10% на все пакеты UC!"
    text += "\n🎁 Промокод: SUMMER2024"
    text += "\n⏰ Действует до конца месяца"
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text=get_text("button.use_promo", user.language_code),
        callback_data="use_promo_code"
    ))
    
    await message.answer(text, reply_markup=keyboard.as_markup())


# Admin commands
@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Admin panel access"""
    if not settings.is_admin(message.from_user.id):
        await message.answer("❌ У вас нет прав администратора")
        return
    
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(
        text="📊 Статистика",
        callback_data="admin_stats"
    ))
    keyboard.add(InlineKeyboardButton(
        text="📦 Заказы",
        callback_data="admin_orders"
    ))
    keyboard.add(InlineKeyboardButton(
        text="👥 Пользователи",
        callback_data="admin_users"
    ))
    keyboard.add(InlineKeyboardButton(
        text="🎫 Промокоды",
        callback_data="admin_promos"
    ))
    keyboard.adjust(2)
    
    await message.answer("🔧 Админ-панель", reply_markup=keyboard.as_markup())


async def main():
    """Main function to run the bot"""
    logger.info("🚀 Starting UC Bot...")
    
    # Initialize database
    from database.database import init_db
    await init_db()
    
    # Start polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())