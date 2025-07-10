"""
Logging utilities for UC Bot
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime

from loguru import logger as loguru_logger
from config.settings import settings


class UCBotLogger:
    """Custom logger for UC Bot"""
    
    def __init__(self):
        self._setup_loguru()
    
    def _setup_loguru(self):
        """Setup loguru logger"""
        # Remove default logger
        loguru_logger.remove()
        
        # Console handler
        loguru_logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True
        )
        
        # File handler
        if settings.LOG_FILE:
            log_file = Path(settings.LOG_FILE)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            loguru_logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                level=settings.LOG_LEVEL,
                rotation="10 MB",
                retention="7 days",
                compression="zip"
            )
        
        # Sentry integration if configured
        if settings.SENTRY_DSN:
            try:
                import sentry_sdk
                from sentry_sdk.integrations.logging import LoggingIntegration
                
                sentry_logging = LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                )
                
                sentry_sdk.init(
                    dsn=settings.SENTRY_DSN,
                    integrations=[sentry_logging],
                    traces_sample_rate=0.1
                )
                
                loguru_logger.info("✅ Sentry integration enabled")
                
            except ImportError:
                loguru_logger.warning("⚠️ Sentry SDK not installed, skipping Sentry integration")
    
    def info(self, message: str):
        """Log info message"""
        loguru_logger.info(message)
    
    def warning(self, message: str):
        """Log warning message"""
        loguru_logger.warning(message)
    
    def error(self, message: str):
        """Log error message"""
        loguru_logger.error(message)
    
    def debug(self, message: str):
        """Log debug message"""
        loguru_logger.debug(message)
    
    def critical(self, message: str):
        """Log critical message"""
        loguru_logger.critical(message)


# Global logger instance
logger = UCBotLogger()


def setup_logger():
    """Setup logging for the application"""
    logger.info("🔧 Logger initialized")


class LoggerMixin:
    """Mixin class for adding logging capabilities"""
    
    @property
    def logger(self):
        return logger


def log_user_action(user_id: int, action: str, details: Optional[str] = None):
    """Log user action"""
    message = f"User {user_id} performed action: {action}"
    if details:
        message += f" | Details: {details}"
    logger.info(message)


def log_admin_action(admin_id: int, action: str, resource_type: Optional[str] = None, 
                    resource_id: Optional[str] = None, details: Optional[str] = None):
    """Log admin action"""
    message = f"Admin {admin_id} performed action: {action}"
    if resource_type and resource_id:
        message += f" on {resource_type} {resource_id}"
    if details:
        message += f" | Details: {details}"
    logger.info(message)


def log_payment_event(payment_id: int, order_id: int, event: str, details: Optional[str] = None):
    """Log payment event"""
    message = f"Payment {payment_id} (Order {order_id}): {event}"
    if details:
        message += f" | Details: {details}"
    logger.info(message)


def log_error_with_context(error: Exception, context: dict):
    """Log error with additional context"""
    message = f"Error: {str(error)}"
    for key, value in context.items():
        message += f" | {key}: {value}"
    logger.error(message)