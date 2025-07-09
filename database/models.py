from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum


Base = declarative_base()


class NewsStatus(enum.Enum):
    """Статусы новостей"""
    PENDING = "pending"  # Ожидает обработки
    PROCESSED = "processed"  # Обработана ИИ
    PUBLISHED = "published"  # Опубликована
    REJECTED = "rejected"  # Отклонена
    ERROR = "error"  # Ошибка обработки


class News(Base):
    """Модель новости"""
    __tablename__ = "news"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Основная информация
    title = Column(String(500), nullable=False, comment="Заголовок новости")
    content = Column(Text, nullable=False, comment="Содержание новости")
    url = Column(String(1000), nullable=True, comment="Ссылка на оригинал")
    
    # Обработанная ИИ информация
    processed_title = Column(String(500), nullable=True, comment="Заголовок после обработки ИИ")
    processed_content = Column(Text, nullable=True, comment="Содержание после обработки ИИ")
    category = Column(String(100), nullable=True, comment="Категория новости")
    emoji = Column(String(10), nullable=True, comment="Эмодзи для новости")
    
    # Мета-информация
    source_id = Column(Integer, ForeignKey("news_sources.id"), nullable=False)
    status = Column(String(20), default=NewsStatus.PENDING.value, comment="Статус новости")
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow, comment="Время создания")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True, comment="Время публикации")
    parsed_at = Column(DateTime, default=datetime.utcnow, comment="Время парсинга")
    
    # Дополнительная информация
    author = Column(String(200), nullable=True, comment="Автор новости")
    image_url = Column(String(1000), nullable=True, comment="Ссылка на изображение")
    tags = Column(JSON, nullable=True, comment="Теги новости")
    
    # ИИ метаданные
    ai_processing_attempts = Column(Integer, default=0, comment="Количество попыток обработки ИИ")
    ai_processing_error = Column(Text, nullable=True, comment="Ошибка обработки ИИ")
    
    # Связи
    source = relationship("NewsSource", back_populates="news")
    
    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title[:50]}...', status='{self.status}')>"


class NewsSource(Base):
    """Модель источника новостей"""
    __tablename__ = "news_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Основная информация
    name = Column(String(200), nullable=False, comment="Название источника")
    url = Column(String(1000), nullable=False, comment="URL источника")
    source_type = Column(String(50), nullable=False, comment="Тип источника (rss, html, api)")
    
    # Настройки парсинга
    enabled = Column(Boolean, default=True, comment="Активен ли источник")
    category = Column(String(100), nullable=True, comment="Категория по умолчанию")
    parsing_config = Column(JSON, nullable=True, comment="Конфигурация парсинга")
    
    # Статистика
    last_parsed_at = Column(DateTime, nullable=True, comment="Последний раз парсился")
    total_news_count = Column(Integer, default=0, comment="Общее количество новостей")
    success_count = Column(Integer, default=0, comment="Успешно спарсено")
    error_count = Column(Integer, default=0, comment="Ошибок парсинга")
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Настройки обработки
    use_ai_processing = Column(Boolean, default=True, comment="Использовать ИИ обработку")
    auto_publish = Column(Boolean, default=False, comment="Автоматически публиковать")
    
    # Связи
    news = relationship("News", back_populates="source")
    
    def __repr__(self):
        return f"<NewsSource(id={self.id}, name='{self.name}', enabled={self.enabled})>"


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Telegram информация
    telegram_id = Column(Integer, unique=True, nullable=False, comment="Telegram ID пользователя")
    username = Column(String(100), nullable=True, comment="Telegram username")
    first_name = Column(String(100), nullable=True, comment="Имя пользователя")
    last_name = Column(String(100), nullable=True, comment="Фамилия пользователя")
    
    # Права доступа
    is_admin = Column(Boolean, default=False, comment="Администратор ли")
    is_active = Column(Boolean, default=True, comment="Активен ли пользователь")
    
    # Статистика
    last_activity = Column(DateTime, default=datetime.utcnow, comment="Последняя активность")
    command_count = Column(Integer, default=0, comment="Количество использованных команд")
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, is_admin={self.is_admin})>"


class BotSettings(Base):
    """Настройки бота"""
    __tablename__ = "bot_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Ключ-значение настроек
    key = Column(String(100), unique=True, nullable=False, comment="Ключ настройки")
    value = Column(Text, nullable=True, comment="Значение настройки")
    description = Column(Text, nullable=True, comment="Описание настройки")
    
    # Мета-информация
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<BotSettings(key='{self.key}', value='{self.value}')>"


class ParsedURL(Base):
    """Модель для отслеживания уже спарсенных URL"""
    __tablename__ = "parsed_urls"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # URL информация
    url = Column(String(1000), unique=True, nullable=False, comment="URL новости")
    url_hash = Column(String(64), unique=True, nullable=False, comment="Хэш URL для быстрого поиска")
    
    # Связь с новостью
    news_id = Column(Integer, ForeignKey("news.id"), nullable=True)
    source_id = Column(Integer, ForeignKey("news_sources.id"), nullable=False)
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<ParsedURL(id={self.id}, url='{self.url[:50]}...')>"


class AIProcessingLog(Base):
    """Лог обработки ИИ"""
    __tablename__ = "ai_processing_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Связь с новостью
    news_id = Column(Integer, ForeignKey("news.id"), nullable=False)
    
    # Информация об обработке
    ai_provider = Column(String(50), nullable=False, comment="Провайдер ИИ (claude, gigachat, openai)")
    input_data = Column(JSON, nullable=False, comment="Входные данные")
    output_data = Column(JSON, nullable=True, comment="Результат обработки")
    
    # Статус
    success = Column(Boolean, default=False, comment="Успешна ли обработка")
    error_message = Column(Text, nullable=True, comment="Сообщение об ошибке")
    
    # Метрики
    processing_time_ms = Column(Integer, nullable=True, comment="Время обработки в мс")
    tokens_used = Column(Integer, nullable=True, comment="Количество использованных токенов")
    
    # Временные метки
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<AIProcessingLog(id={self.id}, news_id={self.news_id}, provider='{self.ai_provider}')>"