import asyncio
import telegram
from telegram import Bot
from telegram.error import TelegramError
from typing import Optional, Dict, Any

from config.settings import settings
from database.database import db_manager, NewsService
from database.models import News, NewsStatus
from utils.logger import logger, log_telegram_action


class TelegramPublisher:
    """Класс для публикации новостей в Telegram канал"""
    
    def __init__(self):
        """Инициализация Telegram бота"""
        self.bot = None
        self._initialize_bot()
    
    def _initialize_bot(self):
        """Инициализация Telegram бота"""
        try:
            if settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
                self.bot = Bot(token=settings.TELEGRAM_BOT_TOKEN)
                logger.info("Telegram бот инициализирован")
            else:
                logger.error("Telegram токен не настроен")
        except Exception as e:
            logger.error(f"Ошибка инициализации Telegram бота: {e}")
    
    def is_available(self) -> bool:
        """Проверка доступности бота"""
        return self.bot is not None
    
    async def test_connection(self) -> bool:
        """Тестирование подключения к Telegram"""
        if not self.is_available():
            return False
        
        try:
            me = await self.bot.get_me()
            logger.info(f"Подключение к Telegram успешно: @{me.username}")
            return True
        except Exception as e:
            logger.error(f"Ошибка подключения к Telegram: {e}")
            return False
    
    def format_news_message(self, news: News) -> str:
        """Форматирование новости для публикации"""
        try:
            # Используем обработанные ИИ данные или оригинальные
            title = news.processed_title or news.title
            content = news.processed_content or news.content
            category = news.category or "Общие новости"
            emoji = news.emoji or settings.CATEGORIES.get(category, "📰")
            
            # Ограничиваем длину для Telegram
            if len(title) > 100:
                title = title[:97] + "..."
            
            if len(content) > 900:
                content = content[:897] + "..."
            
            # Формируем сообщение
            message = f"{emoji} <b>{title}</b>\n\n"
            message += f"{content}\n\n"
            
            # Добавляем категорию
            message += f"#{category.replace(' ', '_')}"
            
            # Добавляем ссылку на источник если есть
            if news.url:
                message += f"\n\n🔗 <a href='{news.url}'>Читать полностью</a>"
            
            return message
            
        except Exception as e:
            logger.error(f"Ошибка форматирования новости {news.id}: {e}")
            return f"📰 <b>Ошибка форматирования новости</b>\n\n{news.title}"
    
    async def publish_news(self, news_id: int) -> bool:
        """Публикация новости в канал"""
        if not self.is_available():
            logger.error("Telegram бот недоступен для публикации")
            return False
        
        try:
            with db_manager.get_session() as session:
                # Получаем новость
                news = session.query(News).filter(News.id == news_id).first()
                if not news:
                    logger.error(f"Новость {news_id} не найдена")
                    return False
                
                # Проверяем статус
                if news.status == NewsStatus.PUBLISHED.value:
                    logger.warning(f"Новость {news_id} уже опубликована")
                    return True
                
                # Форматируем сообщение
                message = self.format_news_message(news)
                
                # Публикуем в канал
                sent_message = await self.bot.send_message(
                    chat_id=settings.TELEGRAM_CHANNEL_ID,
                    text=message,
                    parse_mode='HTML',
                    disable_web_page_preview=False
                )
                
                # Обновляем статус новости
                NewsService.update_news_status(session, news_id, NewsStatus.PUBLISHED.value)
                
                log_telegram_action("publish_news", chat_id=settings.TELEGRAM_CHANNEL_ID)
                logger.info(f"Новость {news_id} успешно опубликована: {sent_message.message_id}")
                
                return True
                
        except TelegramError as e:
            log_telegram_action("publish_news", chat_id=settings.TELEGRAM_CHANNEL_ID, 
                              success=False, error=str(e))
            logger.error(f"Telegram ошибка при публикации новости {news_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка публикации новости {news_id}: {e}")
            return False
    
    async def publish_pending_news(self, limit: int = 5) -> Dict[str, int]:
        """Публикация всех обработанных новостей"""
        if not self.is_available():
            return {"published": 0, "errors": 0}
        
        published_count = 0
        error_count = 0
        
        try:
            with db_manager.get_session() as session:
                # Получаем обработанные новости
                processed_news = NewsService.get_processed_news(session, limit)
                
                for news in processed_news:
                    success = await self.publish_news(news.id)
                    if success:
                        published_count += 1
                    else:
                        error_count += 1
                    
                    # Небольшая пауза между публикациями
                    await asyncio.sleep(1)
                
                logger.info(f"Публикация завершена: {published_count} опубликовано, {error_count} ошибок")
                
        except Exception as e:
            logger.error(f"Ошибка массовой публикации: {e}")
            error_count += 1
        
        return {"published": published_count, "errors": error_count}
    
    async def send_admin_message(self, message: str) -> bool:
        """Отправка сообщения администратору"""
        if not self.is_available():
            return False
        
        try:
            await self.bot.send_message(
                chat_id=settings.ADMIN_USER_ID,
                text=message,
                parse_mode='HTML'
            )
            
            log_telegram_action("send_admin_message", user_id=settings.ADMIN_USER_ID)
            return True
            
        except Exception as e:
            log_telegram_action("send_admin_message", user_id=settings.ADMIN_USER_ID, 
                              success=False, error=str(e))
            logger.error(f"Ошибка отправки сообщения админу: {e}")
            return False
    
    async def notify_admin_about_news(self, news_count: int, source_name: str):
        """Уведомление админа о новых новостях"""
        message = f"📰 <b>Новые новости обработаны!</b>\n\n"
        message += f"🔢 Количество: {news_count}\n"
        message += f"📡 Источник: {source_name}\n\n"
        message += f"Используйте команды для управления публикацией."
        
        await self.send_admin_message(message)


# Глобальный экземпляр издателя
telegram_publisher = TelegramPublisher()


# Функция для синхронного использования
def publish_news_sync(news_id: int) -> bool:
    """Синхронная обертка для публикации новости"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(telegram_publisher.publish_news(news_id))
    except Exception as e:
        logger.error(f"Ошибка синхронной публикации: {e}")
        return False
    finally:
        loop.close()


def test_telegram_connection() -> bool:
    """Синхронная проверка подключения к Telegram"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(telegram_publisher.test_connection())
    except Exception as e:
        logger.error(f"Ошибка тестирования Telegram: {e}")
        return False
    finally:
        loop.close()