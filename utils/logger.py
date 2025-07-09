import os
import sys
from loguru import logger
from datetime import datetime
from pathlib import Path

# Импортируем настройки (будет работать после создания)
try:
    from config.settings import settings
    LOG_LEVEL = settings.LOG_LEVEL
    LOG_FILE = settings.LOG_FILE
except ImportError:
    # Значения по умолчанию если настройки еще не созданы
    LOG_LEVEL = "INFO"
    LOG_FILE = "logs/bot.log"


def setup_logger():
    """Настройка системы логирования"""
    
    # Удаляем стандартный обработчик
    logger.remove()
    
    # Создаем директорию для логов если не существует
    log_dir = Path(LOG_FILE).parent
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Формат логов
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Добавляем обработчик для консоли
    logger.add(
        sys.stdout,
        format=log_format,
        level=LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Добавляем обработчик для файла
    logger.add(
        LOG_FILE,
        format=log_format,
        level=LOG_LEVEL,
        rotation="10 MB",  # Ротация при достижении 10 МБ
        retention="1 month",  # Хранить логи месяц
        compression="zip",  # Сжимать старые логи
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )
    
    # Добавляем обработчик для критических ошибок
    logger.add(
        "logs/errors.log",
        format=log_format,
        level="ERROR",
        rotation="5 MB",
        retention="3 months",
        compression="zip",
        backtrace=True,
        diagnose=True,
        encoding="utf-8"
    )
    
    logger.info("Система логирования инициализирована")


def log_function_call(func_name: str, args: dict = None, result: str = None):
    """Логирование вызовов функций"""
    if args:
        logger.debug(f"Вызов функции {func_name} с аргументами: {args}")
    else:
        logger.debug(f"Вызов функции {func_name}")
    
    if result:
        logger.debug(f"Результат функции {func_name}: {result}")


def log_api_call(api_name: str, endpoint: str, status_code: int = None, 
                response_time: float = None, error: str = None):
    """Логирование API вызовов"""
    if error:
        logger.error(f"API {api_name} [{endpoint}] - Ошибка: {error}")
    elif status_code:
        if response_time:
            logger.info(f"API {api_name} [{endpoint}] - {status_code} ({response_time:.2f}s)")
        else:
            logger.info(f"API {api_name} [{endpoint}] - {status_code}")
    else:
        logger.info(f"API {api_name} [{endpoint}] - Запрос отправлен")


def log_parsing_result(source_name: str, success_count: int, error_count: int, 
                      total_time: float = None):
    """Логирование результатов парсинга"""
    if total_time:
        logger.info(
            f"Парсинг {source_name}: успешно={success_count}, ошибок={error_count}, "
            f"время={total_time:.2f}s"
        )
    else:
        logger.info(f"Парсинг {source_name}: успешно={success_count}, ошибок={error_count}")


def log_ai_processing(news_id: int, ai_provider: str, success: bool, 
                     processing_time: float = None, error: str = None):
    """Логирование обработки ИИ"""
    if success:
        if processing_time:
            logger.info(f"ИИ обработка [{ai_provider}] новости {news_id} - Успешно ({processing_time:.2f}s)")
        else:
            logger.info(f"ИИ обработка [{ai_provider}] новости {news_id} - Успешно")
    else:
        logger.error(f"ИИ обработка [{ai_provider}] новости {news_id} - Ошибка: {error}")


def log_telegram_action(action: str, user_id: int = None, chat_id: int = None, 
                       success: bool = True, error: str = None):
    """Логирование действий в Telegram"""
    user_info = f"user_id={user_id}" if user_id else ""
    chat_info = f"chat_id={chat_id}" if chat_id else ""
    location = " ".join(filter(None, [user_info, chat_info]))
    
    if success:
        logger.info(f"Telegram [{action}] {location} - Успешно")
    else:
        logger.error(f"Telegram [{action}] {location} - Ошибка: {error}")


class NewsLogger:
    """Специальный логгер для новостей"""
    
    @staticmethod
    def log_news_created(news_id: int, title: str, source: str):
        """Логирование создания новости"""
        logger.info(f"Создана новость {news_id}: '{title[:50]}...' из {source}")
    
    @staticmethod
    def log_news_processed(news_id: int, ai_provider: str):
        """Логирование обработки новости ИИ"""
        logger.info(f"Новость {news_id} обработана ИИ [{ai_provider}]")
    
    @staticmethod
    def log_news_published(news_id: int, channel_id: str):
        """Логирование публикации новости"""
        logger.info(f"Новость {news_id} опубликована в канал {channel_id}")
    
    @staticmethod
    def log_news_rejected(news_id: int, reason: str):
        """Логирование отклонения новости"""
        logger.warning(f"Новость {news_id} отклонена: {reason}")


class PerformanceLogger:
    """Логгер для мониторинга производительности"""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        logger.debug(f"Начало операции: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            if exc_type:
                logger.error(f"Операция {self.operation_name} завершена с ошибкой за {duration:.2f}s")
            else:
                logger.debug(f"Операция {self.operation_name} завершена за {duration:.2f}s")


# Инициализируем логгер при импорте
setup_logger()


# Экспортируем основной логгер
__all__ = ['logger', 'log_function_call', 'log_api_call', 'log_parsing_result', 
           'log_ai_processing', 'log_telegram_action', 'NewsLogger', 'PerformanceLogger']