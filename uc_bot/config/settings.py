"""
UC Bot Configuration Settings
"""
import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseSettings, Field, validator


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # App Info
    APP_NAME: str = "UC Bot"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Telegram bot for PUBG Mobile UC sales"
    
    # Telegram Settings
    TELEGRAM_BOT_TOKEN: str = Field(..., env="TELEGRAM_BOT_TOKEN")
    TELEGRAM_WEBHOOK_URL: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_URL")
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = Field(None, env="TELEGRAM_WEBHOOK_SECRET")
    
    # Admin Settings
    ADMIN_USER_IDS: List[int] = Field(default_factory=list, env="ADMIN_USER_IDS")
    SUPER_ADMIN_ID: int = Field(..., env="SUPER_ADMIN_ID")
    
    @validator("ADMIN_USER_IDS", pre=True)
    def parse_admin_ids(cls, v):
        if isinstance(v, str):
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        return v
    
    # Database Settings
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DATABASE_ECHO: bool = Field(False, env="DATABASE_ECHO")
    
    # Redis Settings
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")
    
    # Web Admin Panel
    ADMIN_PANEL_SECRET_KEY: str = Field(..., env="ADMIN_PANEL_SECRET_KEY")
    ADMIN_PANEL_HOST: str = Field("0.0.0.0", env="ADMIN_PANEL_HOST")
    ADMIN_PANEL_PORT: int = Field(8000, env="ADMIN_PANEL_PORT")
    ADMIN_PANEL_DEBUG: bool = Field(False, env="ADMIN_PANEL_DEBUG")
    
    # JWT Settings
    JWT_SECRET_KEY: str = Field(..., env="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Payment Providers
    STRIPE_SECRET_KEY: Optional[str] = Field(None, env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(None, env="STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(None, env="STRIPE_WEBHOOK_SECRET")
    
    PAYPAL_CLIENT_ID: Optional[str] = Field(None, env="PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET: Optional[str] = Field(None, env="PAYPAL_CLIENT_SECRET")
    PAYPAL_SANDBOX: bool = Field(True, env="PAYPAL_SANDBOX")
    
    CRYPTOPAY_API_TOKEN: Optional[str] = Field(None, env="CRYPTOPAY_API_TOKEN")
    BLOCKCHAIN_API_KEY: Optional[str] = Field(None, env="BLOCKCHAIN_API_KEY")
    
    QIWI_SECRET_KEY: Optional[str] = Field(None, env="QIWI_SECRET_KEY")
    QIWI_THEME_CODE: Optional[str] = Field(None, env="QIWI_THEME_CODE")
    
    YOOMONEY_CLIENT_ID: Optional[str] = Field(None, env="YOOMONEY_CLIENT_ID")
    YOOMONEY_CLIENT_SECRET: Optional[str] = Field(None, env="YOOMONEY_CLIENT_SECRET")
    
    # PUBG API
    PUBG_API_KEY: Optional[str] = Field(None, env="PUBG_API_KEY")
    PUBG_API_ENDPOINT: str = Field("https://api.pubgmobile.com", env="PUBG_API_ENDPOINT")
    
    # Localization
    DEFAULT_LANGUAGE: str = Field("ru", env="DEFAULT_LANGUAGE")
    SUPPORTED_LANGUAGES: List[str] = Field(["ru", "en", "ar"], env="SUPPORTED_LANGUAGES")
    
    @validator("SUPPORTED_LANGUAGES", pre=True)
    def parse_languages(cls, v):
        if isinstance(v, str):
            return [x.strip() for x in v.split(",") if x.strip()]
        return v
    
    # Security
    ENCRYPTION_KEY: str = Field(..., env="ENCRYPTION_KEY")
    TWO_FACTOR_ISSUER_NAME: str = Field("UC Bot Admin", env="TWO_FACTOR_ISSUER_NAME")
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field("logs/uc_bot.log", env="LOG_FILE")
    
    # Business Settings
    DEFAULT_CURRENCY: str = Field("USD", env="DEFAULT_CURRENCY")
    UC_PRICE_PER_UNIT: float = Field(0.01, env="UC_PRICE_PER_UNIT")
    MIN_ORDER_AMOUNT: int = Field(1, env="MIN_ORDER_AMOUNT")
    MAX_ORDER_AMOUNT: int = Field(50000, env="MAX_ORDER_AMOUNT")
    
    # Referral System
    REFERRAL_BONUS_PERCENT: float = Field(5.0, env="REFERRAL_BONUS_PERCENT")
    REFERRAL_MIN_ORDER: int = Field(10, env="REFERRAL_MIN_ORDER")
    
    # Anti-Fraud
    MAX_ORDERS_PER_HOUR: int = Field(5, env="MAX_ORDERS_PER_HOUR")
    SUSPICIOUS_ORDER_THRESHOLD: int = Field(100, env="SUSPICIOUS_ORDER_THRESHOLD")
    
    # File Storage
    UPLOAD_PATH: str = Field("uploads/", env="UPLOAD_PATH")
    MAX_FILE_SIZE: int = Field(5242880, env="MAX_FILE_SIZE")  # 5MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def project_root(self) -> Path:
        """Корневая директория проекта"""
        return Path(__file__).parent.parent

    @property
    def upload_dir(self) -> Path:
        """Директория для загрузок"""
        upload_path = self.project_root / self.UPLOAD_PATH
        upload_path.mkdir(exist_ok=True)
        return upload_path

    @property
    def logs_dir(self) -> Path:
        """Директория для логов"""
        log_path = Path(self.LOG_FILE).parent
        if not log_path.is_absolute():
            log_path = self.project_root / log_path
        log_path.mkdir(exist_ok=True)
        return log_path

    def get_payment_providers(self) -> List[str]:
        """Получить список доступных платежных провайдеров"""
        providers = []
        
        if self.STRIPE_SECRET_KEY:
            providers.append("stripe")
        if self.PAYPAL_CLIENT_ID:
            providers.append("paypal")
        if self.CRYPTOPAY_API_TOKEN:
            providers.append("crypto")
        if self.QIWI_SECRET_KEY:
            providers.append("qiwi")
        if self.YOOMONEY_CLIENT_ID:
            providers.append("yoomoney")
            
        return providers

    def is_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь администратором"""
        return user_id == self.SUPER_ADMIN_ID or user_id in self.ADMIN_USER_IDS

    def is_super_admin(self, user_id: int) -> bool:
        """Проверить, является ли пользователь супер-администратором"""
        return user_id == self.SUPER_ADMIN_ID


# Глобальная переменная настроек
settings = Settings()

# UC Products Configuration
UC_PRODUCTS = [
    {"amount": 60, "price": 0.99, "bonus": 0, "popular": False},
    {"amount": 300, "price": 4.99, "bonus": 25, "popular": False},
    {"amount": 600, "price": 9.99, "bonus": 60, "popular": True},
    {"amount": 1500, "price": 24.99, "bonus": 300, "popular": True},
    {"amount": 3000, "price": 49.99, "bonus": 700, "popular": False},
    {"amount": 6000, "price": 99.99, "bonus": 1500, "popular": False},
    {"amount": 12000, "price": 199.99, "bonus": 3500, "popular": False},
]

# Supported Currencies
SUPPORTED_CURRENCIES = {
    "USD": {"symbol": "$", "name": "US Dollar"},
    "EUR": {"symbol": "€", "name": "Euro"},
    "RUB": {"symbol": "₽", "name": "Russian Ruble"},
    "UAH": {"symbol": "₴", "name": "Ukrainian Hryvnia"},
}

# Payment Methods Configuration
PAYMENT_METHODS = {
    "stripe": {
        "name": "Credit Card",
        "icon": "💳",
        "enabled": True,
        "currencies": ["USD", "EUR"],
        "min_amount": 1,
        "max_amount": 10000,
    },
    "paypal": {
        "name": "PayPal",
        "icon": "💰",
        "enabled": True,
        "currencies": ["USD", "EUR"],
        "min_amount": 5,
        "max_amount": 10000,
    },
    "crypto": {
        "name": "Cryptocurrency",
        "icon": "₿",
        "enabled": True,
        "currencies": ["USDT", "BTC", "ETH"],
        "min_amount": 10,
        "max_amount": 50000,
    },
    "qiwi": {
        "name": "QIWI Wallet",
        "icon": "🥝",
        "enabled": True,
        "currencies": ["RUB"],
        "min_amount": 100,
        "max_amount": 100000,
    },
}