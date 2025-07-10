#!/usr/bin/env python3
"""
UC Bot - Telegram bot for PUBG Mobile UC sales
Main entry point for the application
"""

import asyncio
import sys
import signal
import logging
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from config.settings import settings
from utils.logger import setup_logger, logger
from database.database import init_db
from bot.main import main as start_bot


class UCBot:
    """Main UC Bot application class"""
    
    def __init__(self):
        self.is_running = False
        self.components_initialized = False
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("💎 UC Bot initializing...")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    async def initialize_components(self):
        """Initialize all system components"""
        try:
            logger.info("🔧 Initializing components...")
            
            # 1. Validate settings
            self._validate_settings()
            
            # 2. Initialize database
            logger.info("💾 Initializing database...")
            await init_db()
            
            # 3. Check payment providers
            logger.info("💳 Checking payment providers...")
            self._check_payment_providers()
            
            self.components_initialized = True
            logger.info("✅ All components initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Component initialization error: {e}")
            raise
    
    def _validate_settings(self):
        """Validate required settings"""
        logger.info("🔍 Validating settings...")
        
        required_settings = [
            ("TELEGRAM_BOT_TOKEN", "Telegram bot token"),
            ("SUPER_ADMIN_ID", "Super admin ID"),
            ("DATABASE_URL", "Database URL"),
            ("JWT_SECRET_KEY", "JWT secret key"),
            ("ENCRYPTION_KEY", "Encryption key")
        ]
        
        missing_settings = []
        
        for setting_name, description in required_settings:
            value = getattr(settings, setting_name, None)
            if not value or str(value) in ["your_bot_token_here", "0", "your_jwt_secret_key"]:
                missing_settings.append(f"{setting_name} ({description})")
        
        if missing_settings:
            logger.error("❌ Missing required settings:")
            for setting in missing_settings:
                logger.error(f"   - {setting}")
            logger.error("📝 Please configure your .env file")
            raise ValueError("Missing required settings")
        
        # Validate admin settings
        if not settings.ADMIN_USER_IDS and settings.SUPER_ADMIN_ID:
            settings.ADMIN_USER_IDS = [settings.SUPER_ADMIN_ID]
        
        logger.info("✅ Settings validated")
    
    def _check_payment_providers(self):
        """Check available payment providers"""
        providers = settings.get_payment_providers()
        
        if providers:
            logger.info(f"💳 Available payment providers: {', '.join(providers)}")
        else:
            logger.warning("⚠️ No payment providers configured")
            logger.warning("   Bot will work but users cannot make payments")
        
        # Check specific providers
        if settings.STRIPE_SECRET_KEY:
            logger.info("✅ Stripe configured")
        if settings.PAYPAL_CLIENT_ID:
            logger.info("✅ PayPal configured")
        if settings.CRYPTOPAY_API_TOKEN:
            logger.info("✅ CryptoPay configured")
        if settings.QIWI_SECRET_KEY:
            logger.info("✅ QIWI configured")
    
    async def start(self):
        """Start the UC Bot"""
        if self.is_running:
            logger.warning("⚠️ Bot is already running")
            return
        
        try:
            logger.info("🚀 Starting UC Bot...")
            
            # Initialize components if not done yet
            if not self.components_initialized:
                await self.initialize_components()
            
            self.is_running = True
            
            # Print status
            self._print_status()
            
            # Start the bot
            await start_bot()
            
        except KeyboardInterrupt:
            logger.info("🛑 Shutdown requested by user")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Critical error: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Stop the UC Bot"""
        if not self.is_running:
            return
        
        logger.info("🛑 Stopping UC Bot...")
        
        try:
            # Close database connections
            logger.info("💾 Closing database connections...")
            # Database cleanup will be handled by SQLAlchemy
            
            self.is_running = False
            logger.info("✅ UC Bot stopped")
            
        except Exception as e:
            logger.error(f"❌ Error during shutdown: {e}")
    
    def _print_status(self):
        """Print system status"""
        logger.info("=" * 60)
        logger.info("💎 UC BOT STATUS")
        logger.info("=" * 60)
        
        # App info
        logger.info(f"📱 App: {settings.APP_NAME} v{settings.APP_VERSION}")
        logger.info(f"📝 Description: {settings.APP_DESCRIPTION}")
        
        # Components status
        logger.info(f"💾 Database: {'✅ Connected' if self.components_initialized else '❌ Error'}")
        
        # Payment providers
        providers = settings.get_payment_providers()
        logger.info(f"💳 Payment providers: {'✅ ' + ', '.join(providers) if providers else '❌ None configured'}")
        
        # Admin settings
        logger.info(f"👑 Super admin: {settings.SUPER_ADMIN_ID}")
        logger.info(f"👥 Admin users: {len(settings.ADMIN_USER_IDS)}")
        
        # Business settings
        logger.info(f"💰 Default currency: {settings.DEFAULT_CURRENCY}")
        logger.info(f"💎 UC price per unit: ${settings.UC_PRICE_PER_UNIT}")
        
        # Localization
        logger.info(f"🌍 Languages: {', '.join(settings.SUPPORTED_LANGUAGES)}")
        logger.info(f"🏠 Default language: {settings.DEFAULT_LANGUAGE}")
        
        logger.info("=" * 60)
    
    async def test_components(self):
        """Test all system components"""
        logger.info("🧪 Testing system components...")
        
        try:
            # Test database
            await self.initialize_components()
            
            # Test payment providers
            from services.payment_service import PaymentService
            payment_service = PaymentService()
            
            logger.info("✅ All components tested successfully")
            
        except Exception as e:
            logger.error(f"❌ Component test failed: {e}")
            raise
    
    async def create_admin(self, username: str, email: str, password: str):
        """Create admin user"""
        try:
            from database.database import get_session
            from database.models import AdminUser
            from passlib.context import CryptContext
            
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            async with get_session() as session:
                # Check if admin exists
                from sqlalchemy import select
                result = await session.execute(
                    select(AdminUser).where(AdminUser.username == username)
                )
                if result.scalar_one_or_none():
                    logger.error(f"Admin user {username} already exists")
                    return False
                
                # Create admin
                admin = AdminUser(
                    username=username,
                    email=email,
                    hashed_password=pwd_context.hash(password),
                    is_active=True,
                    is_superuser=True
                )
                
                session.add(admin)
                await session.commit()
                
                logger.info(f"✅ Admin user {username} created successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error creating admin: {e}")
            return False


def print_help():
    """Print usage help"""
    help_text = """
💎 UC Bot - PUBG Mobile UC Sales Bot

USAGE:
    python main.py [COMMAND]

COMMANDS:
    start               Start the bot (default)
    test                Test all components
    create-admin        Create admin user
    help                Show this help

EXAMPLES:
    python main.py                      # Start bot
    python main.py test                 # Test components
    python main.py create-admin         # Create admin user

📝 SETUP:
    1. Copy .env.example to .env
    2. Configure all required settings
    3. Set up PostgreSQL database
    4. Configure payment providers
    5. Run: python main.py

🔗 DOCUMENTATION:
    See README.md for detailed setup instructions
    """
    print(help_text)


async def main():
    """Main entry point"""
    # Setup logging
    setup_logger()
    
    # Get command
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    if command in ["help", "--help", "-h"]:
        print_help()
        return
    
    # Create bot instance
    bot = UCBot()
    
    try:
        if command == "start":
            # Start bot normally
            await bot.start()
            
        elif command == "test":
            # Test components
            await bot.test_components()
            logger.info("🧪 All tests completed successfully")
            
        elif command == "create-admin":
            # Create admin user
            print("Creating admin user...")
            username = input("Username: ").strip()
            email = input("Email: ").strip()
            password = input("Password: ").strip()
            
            if not username or not email or not password:
                logger.error("❌ All fields are required")
                sys.exit(1)
            
            await bot.initialize_components()
            success = await bot.create_admin(username, email, password)
            
            if success:
                logger.info("🎉 Admin user created successfully!")
            else:
                sys.exit(1)
                
        else:
            logger.error(f"❌ Unknown command: {command}")
            print("Use 'python main.py help' for usage information")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("🛑 Interrupted by user")
        bot.stop()
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        bot.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())