"""
Database configuration and utilities for UC Bot
"""
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from config.settings import settings
from database.models import Base
from utils.logger import logger


class DatabaseManager:
    """Database manager for UC Bot"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
        self._initialized = False
    
    def initialize(self):
        """Initialize database connection"""
        if self._initialized:
            return
        
        # Create async engine
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DATABASE_ECHO,
            poolclass=StaticPool if settings.DATABASE_URL.startswith("sqlite") else None,
            connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
            future=True
        )
        
        # Create session factory
        self.async_session = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        self._initialized = True
        logger.info("✅ Database connection initialized")
    
    async def create_tables(self):
        """Create all tables"""
        if not self._initialized:
            self.initialize()
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created")
    
    async def drop_tables(self):
        """Drop all tables (use with caution!)"""
        if not self._initialized:
            self.initialize()
        
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.warning("⚠️ All database tables dropped")
    
    async def close(self):
        """Close database connections"""
        if self.engine:
            await self.engine.dispose()
            logger.info("🔌 Database connection closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get database session context manager"""
        if not self._initialized:
            self.initialize()
        
        async with self.async_session() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Global database manager
db_manager = DatabaseManager()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session"""
    async with db_manager.get_session() as session:
        yield session


async def init_db():
    """Initialize database and create tables"""
    try:
        logger.info("🔧 Initializing database...")
        
        # Initialize connection
        db_manager.initialize()
        
        # Create tables
        await db_manager.create_tables()
        
        # Initialize default data
        await _initialize_default_data()
        
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def _initialize_default_data():
    """Initialize default data in database"""
    try:
        from database.models import UCProduct, PromoCode, PromoCodeType, Settings
        from config.settings import UC_PRODUCTS
        from decimal import Decimal
        
        async with get_session() as session:
            # Check if UC products already exist
            from sqlalchemy import select, func
            
            result = await session.execute(select(func.count(UCProduct.id)))
            product_count = result.scalar()
            
            if product_count == 0:
                logger.info("🛍️ Creating default UC products...")
                
                # Create UC products from config
                for i, product_config in enumerate(UC_PRODUCTS):
                    product = UCProduct(
                        amount=product_config["amount"],
                        bonus_amount=product_config.get("bonus", 0),
                        price_usd=Decimal(str(product_config["price"])),
                        name=f"{product_config['amount']} UC",
                        description=f"PUBG Mobile UC Package - {product_config['amount']} UC",
                        is_active=True,
                        is_popular=product_config.get("popular", False),
                        sort_order=i
                    )
                    session.add(product)
                
                await session.commit()
                logger.info(f"✅ Created {len(UC_PRODUCTS)} UC products")
            
            # Check if settings exist
            result = await session.execute(select(func.count(Settings.id)))
            settings_count = result.scalar()
            
            if settings_count == 0:
                logger.info("⚙️ Creating default settings...")
                
                default_settings = [
                    {
                        "key": "bot_status",
                        "value": {"active": True, "maintenance": False},
                        "description": "Bot operational status"
                    },
                    {
                        "key": "welcome_message",
                        "value": {
                            "ru": "Добро пожаловать в UC Bot!",
                            "en": "Welcome to UC Bot!",
                            "ar": "مرحباً بك في UC Bot!"
                        },
                        "description": "Welcome message for new users"
                    },
                    {
                        "key": "payment_methods",
                        "value": {
                            "stripe": True,
                            "paypal": True,
                            "crypto": True,
                            "qiwi": True
                        },
                        "description": "Enabled payment methods"
                    }
                ]
                
                for setting_config in default_settings:
                    setting = Settings(
                        key=setting_config["key"],
                        value=setting_config["value"],
                        description=setting_config["description"]
                    )
                    session.add(setting)
                
                await session.commit()
                logger.info(f"✅ Created {len(default_settings)} default settings")
            
            # Create sample promo code
            result = await session.execute(select(func.count(PromoCode.id)))
            promo_count = result.scalar()
            
            if promo_count == 0:
                logger.info("🎫 Creating sample promo code...")
                
                sample_promo = PromoCode(
                    code="WELCOME10",
                    discount_type=PromoCodeType.PERCENTAGE,
                    discount_value=Decimal("10.0"),
                    max_uses=100,
                    max_uses_per_user=1,
                    min_order_amount=Decimal("5.0"),
                    description="Welcome bonus - 10% discount",
                    is_active=True
                )
                session.add(sample_promo)
                
                await session.commit()
                logger.info("✅ Created sample promo code: WELCOME10")
        
    except Exception as e:
        logger.error(f"❌ Error initializing default data: {e}")
        raise


async def reset_database():
    """Reset database (drop and recreate all tables)"""
    try:
        logger.warning("⚠️ Resetting database...")
        
        # Drop all tables
        await db_manager.drop_tables()
        
        # Create tables again
        await db_manager.create_tables()
        
        # Initialize default data
        await _initialize_default_data()
        
        logger.info("✅ Database reset completed")
        
    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
        raise


async def check_database_health() -> dict:
    """Check database health and connection"""
    try:
        async with get_session() as session:
            # Simple query to test connection
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            result.fetchone()
            
            # Get basic stats
            from database.models import User, Order, Payment
            from sqlalchemy import select, func
            
            user_count = await session.scalar(select(func.count(User.id)))
            order_count = await session.scalar(select(func.count(Order.id)))
            payment_count = await session.scalar(select(func.count(Payment.id)))
            
            return {
                "status": "healthy",
                "connection": True,
                "stats": {
                    "users": user_count or 0,
                    "orders": order_count or 0,
                    "payments": payment_count or 0
                }
            }
            
    except Exception as e:
        logger.error(f"❌ Database health check failed: {e}")
        return {
            "status": "unhealthy",
            "connection": False,
            "error": str(e)
        }


async def backup_database(file_path: str = None):
    """Create database backup (basic implementation)"""
    try:
        if not file_path:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"backup_uc_bot_{timestamp}.sql"
        
        # This is a basic implementation
        # For production, you should use proper database backup tools
        logger.info(f"🗄️ Creating database backup: {file_path}")
        
        # Implementation depends on database type
        # For PostgreSQL: pg_dump
        # For SQLite: copy file
        # For MySQL: mysqldump
        
        logger.warning("⚠️ Backup functionality not fully implemented")
        logger.info("Please use appropriate database backup tools for production")
        
    except Exception as e:
        logger.error(f"❌ Database backup failed: {e}")
        raise