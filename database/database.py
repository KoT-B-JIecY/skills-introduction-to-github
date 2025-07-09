from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import hashlib
from datetime import datetime

from config.settings import settings
from database.models import Base, NewsSource, User, BotSettings
from utils.logger import logger


class DatabaseManager:
    """Менеджер базы данных"""
    
    def __init__(self):
        """Инициализация подключения к БД"""
        # Настройка движка базы данных
        if settings.DATABASE_URL.startswith("sqlite"):
            # Для SQLite добавляем дополнительные параметры
            self.engine = create_engine(
                settings.DATABASE_URL,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                },
                echo=settings.LOG_LEVEL == "DEBUG"
            )
        else:
            # Для других БД (PostgreSQL, MySQL)
            self.engine = create_engine(
                settings.DATABASE_URL,
                echo=settings.LOG_LEVEL == "DEBUG"
            )
        
        # Создание сессии
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"База данных инициализирована: {settings.DATABASE_URL}")
    
    def create_tables(self):
        """Создание всех таблиц"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Таблицы базы данных созданы успешно")
            
            # Создание начальных данных
            self._create_initial_data()
            
        except Exception as e:
            logger.error(f"Ошибка создания таблиц: {e}")
            raise
    
    def _create_initial_data(self):
        """Создание начальных данных"""
        with self.get_session() as session:
            try:
                # Создание администратора
                if settings.ADMIN_USER_ID > 0:
                    admin_user = session.query(User).filter(
                        User.telegram_id == settings.ADMIN_USER_ID
                    ).first()
                    
                    if not admin_user:
                        admin_user = User(
                            telegram_id=settings.ADMIN_USER_ID,
                            is_admin=True,
                            first_name="Админ",
                            username="admin"
                        )
                        session.add(admin_user)
                        logger.info(f"Создан администратор с ID: {settings.ADMIN_USER_ID}")
                
                # Создание источников новостей из конфигурации
                for source_config in settings.NEWS_SOURCES:
                    existing_source = session.query(NewsSource).filter(
                        NewsSource.url == source_config["url"]
                    ).first()
                    
                    if not existing_source:
                        news_source = NewsSource(
                            name=source_config["name"],
                            url=source_config["url"],
                            source_type=source_config["type"],
                            enabled=source_config.get("enabled", True),
                            category=source_config.get("category"),
                            parsing_config=source_config.get("selectors", {})
                        )
                        session.add(news_source)
                        logger.info(f"Создан источник новостей: {source_config['name']}")
                
                # Создание базовых настроек
                default_settings = [
                    {
                        "key": "parsing_enabled",
                        "value": "true",
                        "description": "Включен ли автоматический парсинг"
                    },
                    {
                        "key": "ai_processing_enabled",
                        "value": str(settings.USE_AI_PROCESSING).lower(),
                        "description": "Включена ли обработка ИИ"
                    },
                    {
                        "key": "auto_publish_enabled",
                        "value": str(settings.AUTO_PUBLISH).lower(),
                        "description": "Автоматическая публикация"
                    },
                    {
                        "key": "parsing_interval",
                        "value": str(settings.PARSING_INTERVAL),
                        "description": "Интервал парсинга в минутах"
                    }
                ]
                
                for setting_data in default_settings:
                    existing_setting = session.query(BotSettings).filter(
                        BotSettings.key == setting_data["key"]
                    ).first()
                    
                    if not existing_setting:
                        setting = BotSettings(**setting_data)
                        session.add(setting)
                
                session.commit()
                logger.info("Начальные данные созданы успешно")
                
            except Exception as e:
                session.rollback()
                logger.error(f"Ошибка создания начальных данных: {e}")
                raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Контекстный менеджер для работы с сессией"""
        session = self.SessionLocal()
        try:
            yield session
        except Exception as e:
            session.rollback()
            logger.error(f"Ошибка в сессии базы данных: {e}")
            raise
        finally:
            session.close()
    
    def get_session_sync(self) -> Session:
        """Получение синхронной сессии (закрывать вручную!)"""
        return self.SessionLocal()
    
    def close_engine(self):
        """Закрытие подключения к базе данных"""
        try:
            self.engine.dispose()
            logger.info("Подключение к базе данных закрыто")
        except Exception as e:
            logger.error(f"Ошибка закрытия подключения к БД: {e}")


# Глобальный экземпляр менеджера БД
db_manager = DatabaseManager()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

def get_url_hash(url: str) -> str:
    """Создание хеша URL для быстрого поиска"""
    return hashlib.sha256(url.encode('utf-8')).hexdigest()


def init_database():
    """Инициализация базы данных"""
    try:
        logger.info("Инициализация базы данных...")
        db_manager.create_tables()
        logger.info("База данных инициализирована успешно")
    except Exception as e:
        logger.error(f"Ошибка инициализации базы данных: {e}")
        raise


# ========== CRUD ОПЕРАЦИИ ==========

class NewsService:
    """Сервис для работы с новостями"""
    
    @staticmethod
    def create_news(session: Session, news_data: dict) -> 'News':
        """Создание новости"""
        from database.models import News
        
        news = News(**news_data)
        session.add(news)
        session.commit()
        session.refresh(news)
        return news
    
    @staticmethod
    def get_pending_news(session: Session, limit: int = 10):
        """Получение новостей ожидающих обработки"""
        from database.models import News, NewsStatus
        
        return session.query(News).filter(
            News.status == NewsStatus.PENDING.value
        ).limit(limit).all()
    
    @staticmethod
    def get_processed_news(session: Session, limit: int = 10):
        """Получение обработанных новостей"""
        from database.models import News, NewsStatus
        
        return session.query(News).filter(
            News.status == NewsStatus.PROCESSED.value
        ).limit(limit).all()
    
    @staticmethod
    def update_news_status(session: Session, news_id: int, status: str):
        """Обновление статуса новости"""
        from database.models import News
        
        news = session.query(News).filter(News.id == news_id).first()
        if news:
            news.status = status
            if status == "published":
                news.published_at = datetime.utcnow()
            session.commit()
        return news


class SourceService:
    """Сервис для работы с источниками"""
    
    @staticmethod
    def get_active_sources(session: Session):
        """Получение активных источников"""
        return session.query(NewsSource).filter(
            NewsSource.enabled == True
        ).all()
    
    @staticmethod
    def update_source_stats(session: Session, source_id: int, success: bool = True):
        """Обновление статистики источника"""
        source = session.query(NewsSource).filter(NewsSource.id == source_id).first()
        if source:
            source.last_parsed_at = datetime.utcnow()
            if success:
                source.success_count += 1
            else:
                source.error_count += 1
            session.commit()


class UserService:
    """Сервис для работы с пользователями"""
    
    @staticmethod
    def get_or_create_user(session: Session, telegram_id: int, **kwargs) -> User:
        """Получение или создание пользователя"""
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            # Проверяем, является ли пользователь администратором
            is_admin = telegram_id == settings.ADMIN_USER_ID or telegram_id in settings.ADMIN_IDS
            
            user = User(
                telegram_id=telegram_id,
                is_admin=is_admin,
                **kwargs
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"Создан новый пользователь: {telegram_id}")
        else:
            # Обновляем время последней активности
            user.last_activity = datetime.utcnow()
            session.commit()
        
        return user
    
    @staticmethod
    def is_admin(session: Session, telegram_id: int) -> bool:
        """Проверка является ли пользователь администратором"""
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        return user and user.is_admin