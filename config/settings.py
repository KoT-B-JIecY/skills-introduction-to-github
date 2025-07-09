import os
from pydantic import BaseSettings
from typing import List, Dict, Any


class Settings(BaseSettings):
    """
    Основные настройки бота
    ВАЖНО: Заполните все необходимые токены и настройки!
    """
    
    # ========== ТЕЛЕГРАМ НАСТРОЙКИ ==========
    # Ваш токен бота (готов к работе)
    TELEGRAM_BOT_TOKEN: str = "7824209469:AAGb-Q0GZVfD4hzzpOiSowbpId4ycBzJqIg"
    
    # ID вашего телеграм канала
    TELEGRAM_CHANNEL_ID: str = "-1002565440601"
    
    # Ваш Telegram ID (администратор)
    ADMIN_USER_ID: int = 8039301345
    
    # Дополнительные админы (ID пользователей)
    ADMIN_IDS: List[int] = []
    
    # ========== ИИ ИНТЕГРАЦИЯ ==========
    # DeepSeek API ключ (готов к работе!)
    DEEPSEEK_API_KEY: str = "sk-825e603c75e444f6b2e73b806d26fd8c"
    
    # Claude API ключ (опционально)
    CLAUDE_API_KEY: str = ""
    
    # GigaChat (опционально)
    GIGACHAT_CLIENT_ID: str = ""
    GIGACHAT_CLIENT_SECRET: str = ""
    
    # OpenAI API ключ (опционально)
    OPENAI_API_KEY: str = ""
    
    # ========== БАЗА ДАННЫХ ==========
    # Путь к базе данных SQLite
    DATABASE_URL: str = "sqlite:///news_bot.db"
    
    # ========== ПАРСИНГ НАСТРОЙКИ ==========
    # Готовые источники новостей (работают сразу!)
    NEWS_SOURCES: List[Dict[str, Any]] = [
        {
            "name": "Лента.ру",
            "url": "https://lenta.ru/rss",
            "type": "rss",
            "enabled": True,
            "category": "Общие новости"
        },
        {
            "name": "РБК",
            "url": "https://rbc.ru/rss/news",
            "type": "rss",
            "enabled": True,
            "category": "Экономика"
        },
        {
            "name": "Ведомости",
            "url": "https://www.vedomosti.ru/rss/news",
            "type": "rss",
            "enabled": True,
            "category": "Экономика"
        },
        {
            "name": "RT Russian",
            "url": "https://russian.rt.com/rss",
            "type": "rss",
            "enabled": True,
            "category": "Мир"
        },
        {
            "name": "Газета.ru",
            "url": "https://www.gazeta.ru/export/rss/lenta.xml",
            "type": "rss",
            "enabled": True,
            "category": "Общие новости"
        }
    ]
    
    # ========== ПЛАНИРОВЩИК ==========
    # Интервал парсинга в минутах
    PARSING_INTERVAL: int = 30
    
    # Максимальное количество новостей за раз
    MAX_NEWS_PER_BATCH: int = 5
    
    # ========== ОБРАБОТКА НОВОСТЕЙ ==========
    # Максимальная длина заголовка
    MAX_TITLE_LENGTH: int = 100
    
    # Максимальная длина текста новости
    MAX_CONTENT_LENGTH: int = 1000
    
    # Использовать ли ИИ для обработки новостей
    USE_AI_PROCESSING: bool = True
    
    # Автоматически публиковать обработанные новости
    AUTO_PUBLISH: bool = False
    
    # ========== КАТЕГОРИИ И СМАЙЛИКИ ==========
    CATEGORIES: Dict[str, str] = {
        "Политика": "🏛️",
        "Экономика": "💰",
        "Технологии": "💻",
        "Спорт": "⚽",
        "Культура": "🎭",
        "Наука": "🔬",
        "Здоровье": "🏥",
        "Общество": "👥",
        "Мир": "🌍",
        "Общие новости": "📰"
    }
    
    # ========== ЛОГИРОВАНИЕ ==========
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/bot.log"
    
    # ========== ПРОКСИ (опционально) ==========
    USE_PROXY: bool = False
    PROXY_URL: str = ""  # Например: "socks5://127.0.0.1:9050"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Создаем экземпляр настроек
settings = Settings()


# ========== ДОПОЛНИТЕЛЬНЫЕ КОНСТАНТЫ ==========
class Messages:
    """Сообщения бота"""
    
    WELCOME_ADMIN = """
🚀 <b>Добро пожаловать в админ панель News Bot!</b>

📰 Бот готов к работе с парсингом новостей
🤖 ИИ интеграция активна
📊 Админ панель загружена

Используйте /help для просмотра всех команд
    """
    
    HELP_ADMIN = """
🔧 <b>Команды администратора:</b>

📰 <b>Управление новостями:</b>
/start_parsing - Запустить парсинг
/stop_parsing - Остановить парсинг
/manual_parse - Ручной парсинг
/pending_news - Показать неопубликованные новости
/publish_news [id] - Опубликовать новость
/delete_news [id] - Удалить новость

⚙️ <b>Настройки:</b>
/settings - Показать настройки
/sources - Управление источниками
/add_source - Добавить источник
/remove_source [id] - Удалить источник
/categories - Управление категориями

📊 <b>Статистика:</b>
/stats - Общая статистика
/logs - Показать логи
/status - Статус системы

🤖 <b>ИИ управление:</b>
/ai_settings - Настройки ИИ
/test_ai - Тестировать ИИ
/reprocess_news [id] - Переобработать новость ИИ

🔄 <b>Планировщик:</b>
/scheduler_status - Статус планировщика
/set_interval [минуты] - Установить интервал парсинга
    """


class AIPrompts:
    """Промпты для ИИ обработки"""
    
    NEWS_PROCESSING = """
Ты - редактор новостей. Твоя задача обработать новость для публикации в телеграм канале.

Требования:
1. Создай привлекательный заголовок (до 100 символов)
2. Перепиши новость кратко и понятно (до 1000 символов)
3. Добавь подходящие эмодзи
4. Определи категорию новости
5. Сохрани фактическую точность

Исходная новость:
Заголовок: {title}
Текст: {content}
Источник: {source}

Ответь в формате JSON:
{{
    "title": "обработанный заголовок",
    "content": "обработанный текст",
    "category": "категория",
    "emoji": "основной эмодзи для новости"
}}
"""

    CATEGORIZATION = """
Определи категорию для новости из списка: {categories}

Новость: {text}

Ответь только названием категории.
"""