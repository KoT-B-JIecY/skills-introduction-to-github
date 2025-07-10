"""
Internationalization utilities for UC Bot
"""
from typing import Dict, Any
from config.settings import settings


# Text translations
TRANSLATIONS = {
    "ru": {
        # Menu items
        "menu.buy_uc": "💎 Купить UC",
        "menu.prices": "💰 Цены",
        "menu.support": "📞 Поддержка", 
        "menu.profile": "👤 Профиль",
        "menu.promotions": "🎁 Акции",
        
        # Buttons
        "button.back": "⬅️ Назад",
        "button.cancel": "❌ Отмена",
        "button.confirm": "✅ Подтвердить",
        "button.pay_now": "💳 Оплатить",
        "button.check_payment": "🔄 Проверить оплату",
        "button.use_saved_id": "✅ Использовать сохраненный ID",
        "button.enter_new_id": "✏️ Ввести новый ID",
        "button.use_saved_nickname": "✅ Использовать сохраненный ник",
        "button.enter_new_nickname": "✏️ Ввести новый ник",
        "button.edit_pubg_data": "✏️ Изменить данные PUBG",
        "button.order_history": "📋 История заказов",
        "button.referral_info": "👥 Реферальная система",
        "button.contact_support": "📞 Связаться с поддержкой",
        "button.faq": "❓ FAQ",
        "button.use_promo": "🎫 Использовать промокод",
        
        # Welcome message
        "welcome.message": """🎮 Добро пожаловать в UC Bot, {name}!

💎 Здесь вы можете быстро и безопасно купить UC для PUBG Mobile
🔒 Гарантия безопасности и мгновенная доставка
💳 Поддержка всех популярных способов оплаты

Выберите нужную опцию в меню ниже:""",
        
        # Products
        "products.choose": """💎 Выберите количество UC:

🔥 - популярные пакеты
🎁 - бонусные UC в подарок

Все цены указаны в USD:""",
        
        # Order process
        "order.enter_pubg_id": """💎 Вы выбрали: {amount} UC за ${price}

🎮 Введите ваш PUBG ID:
(9-12 цифр, например: 5123456789)""",
        
        "order.enter_pubg_nickname": """🎮 Введите ваш никнейм в PUBG Mobile:
(3-16 символов)""",
        
        "order.choose_payment": """📋 Подтверждение заказа:

💎 UC: {amount}
💰 Сумма: ${price}
🎮 PUBG ID: {pubg_id}
👤 Никнейм: {nickname}

Выберите способ оплаты:""",
        
        # Payment
        "payment.card": "Банковская карта",
        "payment.crypto": "Криптовалюта",
        "payment.paypal": "PayPal",
        "payment.qiwi": "QIWI Кошелек",
        
        "payment.created": """💳 Платеж создан!

💎 UC: {amount}
💰 Сумма: ${price}
🔄 Способ: {method}

Нажмите кнопку ниже для оплаты:""",
        
        "payment.success": """🎉 Оплата успешна!

💎 {amount} UC будут зачислены на аккаунт PUBG ID: {pubg_id}

Обычно зачисление происходит в течение 1-5 минут.""",
        
        "payment.still_pending": "⏳ Платеж еще обрабатывается...",
        "payment.failed": "❌ Платеж не прошел",
        
        # Prices
        "prices.header": "💰 Актуальные цены на UC:",
        "prices.footer": "💳 Принимаем: карты, криптовалюты, PayPal, QIWI\n🔒 Безопасность гарантирована\n⚡ Доставка в течение 5 минут",
        
        # Profile
        "profile.info": """👤 Ваш профиль:

🏷️ Username: @{username}
📊 Заказов: {total_orders}
💰 Потрачено: ${total_spent}
💎 Куплено UC: {total_uc}
👥 Реферальный код: {referral_code}
💵 Реферальный бонус: ${referral_bonus}""",
        
        # Support
        "support.info": """📞 Поддержка UC Bot

🕐 Работаем 24/7
⚡ Быстрые ответы
🔒 Конфиденциальность

Если у вас есть вопросы или проблемы, свяжитесь с нами:""",
        
        # Promotions
        "promotions.current": "🎁 Текущие акции и промокоды:",
        
        # Errors
        "error.invalid_pubg_id": "❌ Неверный PUBG ID. Введите 9-12 цифр.",
        "error.invalid_nickname": "❌ Неверный никнейм. Используйте 3-16 символов.",
        "error.order_not_found": "❌ Заказ не найден",
        "error.payment_failed": "❌ Ошибка создания платежа",
    },
    
    "en": {
        # Menu items
        "menu.buy_uc": "💎 Buy UC",
        "menu.prices": "💰 Prices",
        "menu.support": "📞 Support",
        "menu.profile": "👤 Profile", 
        "menu.promotions": "🎁 Promotions",
        
        # Buttons
        "button.back": "⬅️ Back",
        "button.cancel": "❌ Cancel",
        "button.confirm": "✅ Confirm",
        "button.pay_now": "💳 Pay Now",
        "button.check_payment": "🔄 Check Payment",
        "button.use_saved_id": "✅ Use Saved ID",
        "button.enter_new_id": "✏️ Enter New ID",
        "button.use_saved_nickname": "✅ Use Saved Nickname",
        "button.enter_new_nickname": "✏️ Enter New Nickname",
        "button.edit_pubg_data": "✏️ Edit PUBG Data",
        "button.order_history": "📋 Order History",
        "button.referral_info": "👥 Referral System",
        "button.contact_support": "📞 Contact Support",
        "button.faq": "❓ FAQ",
        "button.use_promo": "🎫 Use Promo Code",
        
        # Welcome message
        "welcome.message": """🎮 Welcome to UC Bot, {name}!

💎 Here you can quickly and safely buy UC for PUBG Mobile
🔒 Security guarantee and instant delivery
💳 Support for all popular payment methods

Choose the option you need from the menu below:""",
        
        # Products
        "products.choose": """💎 Choose UC amount:

🔥 - popular packages
🎁 - bonus UC as gift

All prices are in USD:""",
        
        # Order process
        "order.enter_pubg_id": """💎 You selected: {amount} UC for ${price}

🎮 Enter your PUBG ID:
(9-12 digits, example: 5123456789)""",
        
        "order.enter_pubg_nickname": """🎮 Enter your PUBG Mobile nickname:
(3-16 characters)""",
        
        "order.choose_payment": """📋 Order confirmation:

💎 UC: {amount}
💰 Amount: ${price}
🎮 PUBG ID: {pubg_id}
👤 Nickname: {nickname}

Choose payment method:""",
        
        # Payment
        "payment.card": "Credit Card",
        "payment.crypto": "Cryptocurrency",
        "payment.paypal": "PayPal",
        "payment.qiwi": "QIWI Wallet",
        
        "payment.created": """💳 Payment created!

💎 UC: {amount}
💰 Amount: ${price}
🔄 Method: {method}

Click the button below to pay:""",
        
        "payment.success": """🎉 Payment successful!

💎 {amount} UC will be credited to PUBG ID: {pubg_id}

Usually crediting takes 1-5 minutes.""",
        
        "payment.still_pending": "⏳ Payment is still processing...",
        "payment.failed": "❌ Payment failed",
        
        # Prices
        "prices.header": "💰 Current UC prices:",
        "prices.footer": "💳 We accept: cards, crypto, PayPal, QIWI\n🔒 Security guaranteed\n⚡ Delivery within 5 minutes",
        
        # Profile
        "profile.info": """👤 Your profile:

🏷️ Username: @{username}
📊 Orders: {total_orders}
💰 Spent: ${total_spent}
💎 UC Purchased: {total_uc}
👥 Referral code: {referral_code}
💵 Referral bonus: ${referral_bonus}""",
        
        # Support
        "support.info": """📞 UC Bot Support

🕐 24/7 Available
⚡ Fast responses
🔒 Confidentiality

If you have questions or problems, contact us:""",
        
        # Promotions
        "promotions.current": "🎁 Current promotions and promo codes:",
        
        # Errors
        "error.invalid_pubg_id": "❌ Invalid PUBG ID. Enter 9-12 digits.",
        "error.invalid_nickname": "❌ Invalid nickname. Use 3-16 characters.",
        "error.order_not_found": "❌ Order not found",
        "error.payment_failed": "❌ Payment creation error",
    },
    
    "ar": {
        # Menu items
        "menu.buy_uc": "💎 شراء UC",
        "menu.prices": "💰 الأسعار",
        "menu.support": "📞 الدعم",
        "menu.profile": "👤 الملف الشخصي",
        "menu.promotions": "🎁 العروض",
        
        # Buttons
        "button.back": "⬅️ رجوع",
        "button.cancel": "❌ إلغاء",
        "button.confirm": "✅ تأكيد",
        "button.pay_now": "💳 ادفع الآن",
        "button.check_payment": "🔄 تحقق من الدفع",
        "button.use_saved_id": "✅ استخدم المعرف المحفوظ",
        "button.enter_new_id": "✏️ أدخل معرف جديد",
        "button.use_saved_nickname": "✅ استخدم الاسم المحفوظ",
        "button.enter_new_nickname": "✏️ أدخل اسم جديد",
        "button.edit_pubg_data": "✏️ تعديل بيانات PUBG",
        "button.order_history": "📋 تاريخ الطلبات",
        "button.referral_info": "👥 نظام الإحالة",
        "button.contact_support": "📞 اتصل بالدعم",
        "button.faq": "❓ الأسئلة الشائعة",
        "button.use_promo": "🎫 استخدم كود الخصم",
        
        # Welcome message
        "welcome.message": """🎮 مرحباً بك في UC Bot، {name}!

💎 هنا يمكنك شراء UC لـ PUBG Mobile بسرعة وأمان
🔒 ضمان الأمان والتسليم الفوري
💳 دعم جميع طرق الدفع الشائعة

اختر الخيار المناسب من القائمة أدناه:""",
        
        # Products
        "products.choose": """💎 اختر كمية UC:

🔥 - الحزم الشائعة
🎁 - UC إضافية كهدية

جميع الأسعار بالدولار الأمريكي:""",
        
        # Order process
        "order.enter_pubg_id": """💎 لقد اخترت: {amount} UC مقابل ${price}

🎮 أدخل معرف PUBG الخاص بك:
(9-12 رقم، مثال: 5123456789)""",
        
        "order.enter_pubg_nickname": """🎮 أدخل اسمك في PUBG Mobile:
(3-16 حرف)""",
        
        "order.choose_payment": """📋 تأكيد الطلب:

💎 UC: {amount}
💰 المبلغ: ${price}
🎮 معرف PUBG: {pubg_id}
👤 الاسم: {nickname}

اختر طريقة الدفع:""",
        
        # Payment
        "payment.card": "البطاقة المصرفية",
        "payment.crypto": "العملة المشفرة",
        "payment.paypal": "PayPal",
        "payment.qiwi": "محفظة QIWI",
        
        "payment.created": """💳 تم إنشاء الدفع!

💎 UC: {amount}
💰 المبلغ: ${price}
🔄 الطريقة: {method}

اضغط الزر أدناه للدفع:""",
        
        "payment.success": """🎉 تم الدفع بنجاح!

💎 {amount} UC سيتم إضافتها لمعرف PUBG: {pubg_id}

عادة ما يستغرق الإيداع 1-5 دقائق.""",
        
        "payment.still_pending": "⏳ الدفع قيد المعالجة...",
        "payment.failed": "❌ فشل الدفع",
        
        # Prices
        "prices.header": "💰 أسعار UC الحالية:",
        "prices.footer": "💳 نقبل: البطاقات، العملات المشفرة، PayPal، QIWI\n🔒 الأمان مضمون\n⚡ التسليم خلال 5 دقائق",
        
        # Profile
        "profile.info": """👤 ملفك الشخصي:

🏷️ اسم المستخدم: @{username}
📊 الطلبات: {total_orders}
💰 المبلغ المنفق: ${total_spent}
💎 UC المشتراة: {total_uc}
👥 كود الإحالة: {referral_code}
💵 مكافأة الإحالة: ${referral_bonus}""",
        
        # Support
        "support.info": """📞 دعم UC Bot

🕐 متوفر 24/7
⚡ ردود سريعة
🔒 السرية

إذا كان لديك أسئلة أو مشاكل، اتصل بنا:""",
        
        # Promotions
        "promotions.current": "🎁 العروض وأكواد الخصم الحالية:",
        
        # Errors
        "error.invalid_pubg_id": "❌ معرف PUBG غير صحيح. أدخل 9-12 رقم.",
        "error.invalid_nickname": "❌ اسم غير صحيح. استخدم 3-16 حرف.",
        "error.order_not_found": "❌ الطلب غير موجود",
        "error.payment_failed": "❌ خطأ في إنشاء الدفع",
    }
}


def get_text(key: str, language: str = None) -> str:
    """Get translated text by key"""
    if language is None:
        language = settings.DEFAULT_LANGUAGE
    
    # Fallback to default language if requested language not available
    if language not in TRANSLATIONS:
        language = settings.DEFAULT_LANGUAGE
    
    # Get translation
    translation = TRANSLATIONS.get(language, {}).get(key)
    
    # Fallback to English if key not found
    if translation is None:
        translation = TRANSLATIONS.get("en", {}).get(key)
    
    # Ultimate fallback to key itself
    if translation is None:
        translation = key
    
    return translation


def get_supported_languages() -> list:
    """Get list of supported languages"""
    return list(TRANSLATIONS.keys())


def set_user_language(user_id: int, language: str):
    """Set user language preference (placeholder for future implementation)"""
    # This could be stored in database or cache
    pass


def get_user_language(user_id: int) -> str:
    """Get user language preference (placeholder for future implementation)"""
    # This could be retrieved from database or cache
    return settings.DEFAULT_LANGUAGE


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount"""
    currency_symbols = {
        "USD": "$",
        "EUR": "€",
        "RUB": "₽",
        "UAH": "₴"
    }
    
    symbol = currency_symbols.get(currency, currency)
    
    if currency == "USD":
        return f"${amount:.2f}"
    elif currency == "EUR":
        return f"€{amount:.2f}"
    elif currency == "RUB":
        return f"{amount:.0f}₽"
    elif currency == "UAH":
        return f"{amount:.0f}₴"
    else:
        return f"{amount:.2f} {currency}"


def format_uc_amount(amount: int, bonus: int = 0) -> str:
    """Format UC amount with bonus"""
    if bonus > 0:
        return f"{amount:,} UC + {bonus:,} 🎁"
    else:
        return f"{amount:,} UC"


def localize_number(number: int, language: str = None) -> str:
    """Localize number formatting"""
    if language is None:
        language = settings.DEFAULT_LANGUAGE
    
    # Use appropriate number formatting for the language
    if language == "ar":
        # Arabic uses Eastern Arabic numerals in some contexts
        return f"{number:,}".replace(",", "٬")
    else:
        return f"{number:,}"