"""
Database Models for UC Bot
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from decimal import Decimal

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, ForeignKey,
    Numeric, Enum, JSON, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum


Base = declarative_base()


class UserStatus(enum.Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    SUSPENDED = "suspended"


class OrderStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing" 
    PAID = "paid"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentMethod(enum.Enum):
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CRYPTO = "crypto"
    QIWI = "qiwi"
    YOOMONEY = "yoomoney"


class PromoCodeType(enum.Enum):
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_UC = "free_uc"


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(String(20), unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    language_code = Column(String(10), default="ru")
    
    # Status and permissions
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    is_admin = Column(Boolean, default=False)
    is_banned = Column(Boolean, default=False)
    
    # Game info
    pubg_id = Column(String(255), nullable=True)
    pubg_nickname = Column(String(255), nullable=True)
    
    # Referral system
    referral_code = Column(String(20), unique=True, nullable=True, index=True)
    referred_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    referral_bonus = Column(Numeric(10, 2), default=0)
    
    # Statistics
    total_orders = Column(Integer, default=0)
    total_spent = Column(Numeric(10, 2), default=0)
    total_uc_purchased = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    orders = relationship("Order", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    referred_users = relationship("User", back_populates="referrer")
    referrer = relationship("User", remote_side=[id], back_populates="referred_users")
    promo_code_uses = relationship("PromoCodeUse", back_populates="user")
    
    def __str__(self):
        return f"User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})"


class UCProduct(Base):
    """Модель товара (UC пакеты)"""
    __tablename__ = "uc_products"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, nullable=False)  # Количество UC
    bonus_amount = Column(Integer, default=0)  # Бонусные UC
    price_usd = Column(Numeric(10, 2), nullable=False)
    price_eur = Column(Numeric(10, 2), nullable=True)
    price_rub = Column(Numeric(10, 2), nullable=True)
    
    # Product info
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    
    # Status and visibility
    is_active = Column(Boolean, default=True)
    is_popular = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    
    # Display order
    sort_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
    
    @property
    def total_uc(self):
        """Общее количество UC включая бонус"""
        return self.amount + self.bonus_amount
    
    def get_price(self, currency: str = "USD") -> Decimal:
        """Получить цену в указанной валюте"""
        if currency == "USD":
            return self.price_usd
        elif currency == "EUR":
            return self.price_eur or self.price_usd
        elif currency == "RUB":
            return self.price_rub or self.price_usd * 90
        return self.price_usd
    
    def __str__(self):
        return f"UCProduct(id={self.id}, amount={self.amount}, price=${self.price_usd})"


class Order(Base):
    """Модель заказа"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # User and order info
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    
    # PUBG account info
    pubg_id = Column(String(255), nullable=False)
    pubg_nickname = Column(String(255), nullable=True)
    
    # Pricing
    total_amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    discount_amount = Column(Numeric(10, 2), default=0)
    final_amount = Column(Numeric(10, 2), nullable=False)
    
    # Delivery
    delivery_method = Column(String(50), default="auto")  # auto, manual
    delivery_status = Column(String(50), default="pending")
    delivery_code = Column(String(500), nullable=True)  # UC redeem code
    delivery_instructions = Column(Text, nullable=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    admin_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order")
    promo_code_use = relationship("PromoCodeUse", back_populates="order", uselist=False)
    
    @property
    def total_uc(self):
        """Общее количество UC в заказе"""
        return sum(item.total_uc for item in self.items)
    
    def __str__(self):
        return f"Order(id={self.id}, user_id={self.user_id}, status={self.status.value})"


class OrderItem(Base):
    """Элемент заказа"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("uc_products.id"), nullable=False)
    
    quantity = Column(Integer, default=1)
    unit_price = Column(Numeric(10, 2), nullable=False)
    total_price = Column(Numeric(10, 2), nullable=False)
    
    # UC amounts at time of purchase
    uc_amount = Column(Integer, nullable=False)
    bonus_uc_amount = Column(Integer, default=0)
    
    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("UCProduct", back_populates="order_items")
    
    @property
    def total_uc(self):
        """Общее количество UC в этом элементе"""
        return (self.uc_amount + self.bonus_uc_amount) * self.quantity
    
    def __str__(self):
        return f"OrderItem(id={self.id}, order_id={self.order_id}, uc_amount={self.uc_amount})"


class Payment(Base):
    """Модель платежа"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(UUID(as_uuid=True), default=uuid.uuid4, unique=True, index=True)
    
    # Relations
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Payment info
    method = Column(Enum(PaymentMethod), nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, index=True)
    
    # Amounts
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    
    # External payment system data
    external_id = Column(String(255), nullable=True, index=True)
    external_data = Column(JSON, nullable=True)
    
    # Gateway response
    gateway_response = Column(JSON, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    order = relationship("Order", back_populates="payments")
    
    def __str__(self):
        return f"Payment(id={self.id}, method={self.method.value}, status={self.status.value})"


class PromoCode(Base):
    """Модель промокода"""
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)
    
    # Discount info
    discount_type = Column(Enum(PromoCodeType), nullable=False)
    discount_value = Column(Numeric(10, 2), nullable=False)  # Percentage or fixed amount
    discount_uc = Column(Integer, default=0)  # Free UC amount
    
    # Usage limits
    max_uses = Column(Integer, nullable=True)  # None = unlimited
    max_uses_per_user = Column(Integer, default=1)
    current_uses = Column(Integer, default=0)
    
    # Validity
    is_active = Column(Boolean, default=True)
    valid_from = Column(DateTime(timezone=True), default=datetime.utcnow)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Conditions
    min_order_amount = Column(Numeric(10, 2), default=0)
    applicable_products = Column(JSON, nullable=True)  # List of product IDs
    
    # Metadata
    description = Column(Text, nullable=True)
    created_by_admin_id = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uses = relationship("PromoCodeUse", back_populates="promo_code")
    
    def is_valid(self) -> bool:
        """Проверить, действителен ли промокод"""
        now = datetime.now(timezone.utc)
        
        if not self.is_active:
            return False
        
        if self.valid_from and now < self.valid_from:
            return False
        
        if self.valid_until and now > self.valid_until:
            return False
        
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        
        return True
    
    def __str__(self):
        return f"PromoCode(id={self.id}, code={self.code}, type={self.discount_type.value})"


class PromoCodeUse(Base):
    """Использование промокода"""
    __tablename__ = "promo_code_uses"

    id = Column(Integer, primary_key=True, index=True)
    promo_code_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    discount_amount = Column(Numeric(10, 2), nullable=False)
    used_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    promo_code = relationship("PromoCode", back_populates="uses")
    user = relationship("User", back_populates="promo_code_uses")
    order = relationship("Order", back_populates="promo_code_use")
    
    __table_args__ = (
        UniqueConstraint('promo_code_id', 'order_id', name='_promo_code_order_uc'),
    )


class AdminUser(Base):
    """Модель администратора"""
    __tablename__ = "admin_users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Personal info
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    
    # Permissions
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    permissions = Column(JSON, default=list)  # List of permission strings
    
    # 2FA
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    actions = relationship("AdminAction", back_populates="admin")
    
    def __str__(self):
        return f"AdminUser(id={self.id}, username={self.username})"


class AdminAction(Base):
    """Логирование действий администраторов"""
    __tablename__ = "admin_actions"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("admin_users.id"), nullable=False)
    
    action = Column(String(100), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)  # user, order, product, etc.
    resource_id = Column(String(50), nullable=True)
    
    description = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    
    # Relationships
    admin = relationship("AdminUser", back_populates="actions")
    
    def __str__(self):
        return f"AdminAction(id={self.id}, action={self.action}, admin_id={self.admin_id})"


class Settings(Base):
    """Системные настройки"""
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    value = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __str__(self):
        return f"Settings(key={self.key})"


# Создаем индексы для оптимизации запросов
Index('idx_orders_status_created', Order.status, Order.created_at)
Index('idx_payments_status_created', Payment.status, Payment.created_at)
Index('idx_users_telegram_id', User.telegram_id)
Index('idx_users_referral_code', User.referral_code)
Index('idx_promo_codes_code', PromoCode.code)
Index('idx_admin_actions_created', AdminAction.created_at)